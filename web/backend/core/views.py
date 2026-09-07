"""Endpoints REST del sistema de gestión de participantes."""
from __future__ import annotations

import os
import shutil
import tempfile

from django.core.files import File
from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from . import services
from .models import Certificado, Curso, Inscripcion, Participante
from .serializers import (CargaCertificadoSerializer, CertificadoSerializer,
                          CursoSerializer, ImportacionSerializer,
                          InscripcionSerializer, ParticipanteSerializer,
                          ReporteParticipanteSerializer)

APROBADO = Inscripcion.Estado.APROBADO
FALTO = Inscripcion.Estado.FALTO


class ParticipanteViewSet(viewsets.ModelViewSet):
    """CRUD de participantes con búsqueda insensible a acentos."""
    serializer_class = ParticipanteSerializer
    ordering_fields = ["apellidos", "nombres", "creado_en"]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        termino = self.request.query_params.get("search", "").strip()
        if termino:
            objetivo = services.norm_espacios(termino)
            ids = [p.id for p in queryset
                   if objetivo in services.norm_espacios(
                       f"{p.nombres} {p.apellidos} {p.dni or ''} {p.email or ''}")]
            queryset = queryset.filter(id__in=ids).order_by("apellidos", "nombres")
        return queryset

    def get_queryset(self):
        return Participante.objects.annotate(
            total_cursos=Count("inscripciones", distinct=True),
            total_aprobados=Count("inscripciones", filter=Q(inscripciones__estado=APROBADO), distinct=True),
            total_faltas=Count("inscripciones", filter=Q(inscripciones__estado=FALTO), distinct=True),
        )

    @action(detail=True, methods=["get"])
    def reporte(self, request, pk=None):
        """Reporte detallado del participante."""
        participante = self.get_object()
        return Response(ReporteParticipanteSerializer(
            participante, context={"request": request}).data)


class CursoViewSet(viewsets.ModelViewSet):
    serializer_class = CursoSerializer
    search_fields = ["nombre", "codigo", "instructor"]
    filterset_fields = ["activo"]
    ordering_fields = ["nombre", "fecha_inicio", "creado_en"]

    def get_queryset(self):
        return Curso.objects.annotate(
            total_participantes=Count("inscripciones", distinct=True),
            total_aprobados=Count("inscripciones", filter=Q(inscripciones__estado=APROBADO), distinct=True),
            total_faltas=Count("inscripciones", filter=Q(inscripciones__estado=FALTO), distinct=True),
        )

    @action(detail=True, methods=["get"])
    def participantes(self, request, pk=None):
        qs = Inscripcion.objects.filter(curso=self.get_object()) \
            .select_related("participante", "curso").prefetch_related("certificados")
        return Response(InscripcionSerializer(qs, many=True, context={"request": request}).data)


class InscripcionViewSet(viewsets.ModelViewSet):
    serializer_class = InscripcionSerializer
    filterset_fields = ["curso", "participante", "estado"]
    search_fields = ["participante__nombres", "participante__apellidos", "curso__nombre"]

    def get_queryset(self):
        return Inscripcion.objects.select_related("participante", "curso") \
            .prefetch_related("certificados")


class CertificadoViewSet(viewsets.ModelViewSet):
    serializer_class = CertificadoSerializer
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ["inscripcion"]
    search_fields = ["inscripcion__participante__nombres",
                     "inscripcion__participante__apellidos",
                     "inscripcion__curso__nombre"]

    def get_queryset(self):
        return Certificado.objects.select_related(
            "inscripcion__participante", "inscripcion__curso")

    @action(detail=False, methods=["post"], url_path="cargar")
    def cargar(self, request):
        """Lee el certificado (curso + nombres/apellidos) y lo vincula al participante."""
        serializer = CargaCertificadoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        archivo = serializer.validated_data["archivo"]
        aprobar = serializer.validated_data["aprobar"]

        # Se conserva el nombre original: es una de las fuentes para detectar
        # el curso y el participante cuando el PDF no tiene texto extraíble.
        carpeta_tmp = tempfile.mkdtemp()
        ruta_tmp = os.path.join(carpeta_tmp, os.path.basename(archivo.name))
        with open(ruta_tmp, "wb") as tmp:
            for chunk in archivo.chunks():
                tmp.write(chunk)
        try:
            deteccion = services.analizar_certificado(ruta_tmp)
            if not deteccion.ok:
                return Response({
                    "detectado": False,
                    "mensaje": deteccion.mensaje,
                    "curso_detectado": deteccion.curso.nombre if deteccion.curso else None,
                    "participante_detectado": (deteccion.participante.nombre_completo
                                               if deteccion.participante else None),
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            inscripcion = deteccion.inscripcion
            if aprobar and inscripcion.estado != APROBADO:
                inscripcion.estado = APROBADO
                inscripcion.save(update_fields=["estado"])

            with open(ruta_tmp, "rb") as fh:
                certificado = Certificado.objects.create(
                    inscripcion=inscripcion,
                    curso_detectado=deteccion.curso.nombre,
                    participante_detectado=deteccion.participante.nombre_completo,
                )
                certificado.archivo.save(os.path.basename(archivo.name), File(fh), save=True)
        finally:
            shutil.rmtree(carpeta_tmp, ignore_errors=True)

        return Response({
            "detectado": True,
            "mensaje": deteccion.mensaje,
            "certificado": CertificadoSerializer(certificado, context={"request": request}).data,
        }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def importar_excel(request):
    """Carga participantes, cursos e inscripciones desde un archivo Excel/CSV."""
    serializer = ImportacionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    archivo = serializer.validated_data["archivo"]
    curso_defecto = (serializer.validated_data.get("curso_por_defecto") or "").strip() or None

    try:
        df = services.leer_dataframe(archivo, archivo.name)
    except Exception as exc:  # noqa: BLE001
        return Response({"detail": f"No se pudo leer el archivo: {exc}"},
                        status=status.HTTP_400_BAD_REQUEST)

    resultado = services.importar_dataframe(df, curso_defecto)
    codigo = status.HTTP_200_OK if resultado.inscripciones else status.HTTP_400_BAD_REQUEST
    return Response(resultado.as_dict(), status=codigo)


@api_view(["GET"])
def dashboard(request):
    """Métricas globales para el panel."""
    cursos = Curso.objects.annotate(
        total_participantes=Count("inscripciones", distinct=True),
        total_aprobados=Count("inscripciones", filter=Q(inscripciones__estado=APROBADO), distinct=True),
        total_faltas=Count("inscripciones", filter=Q(inscripciones__estado=FALTO), distinct=True),
    )
    return Response({
        "participantes": Participante.objects.count(),
        "cursos": Curso.objects.count(),
        "cursos_activos": Curso.objects.filter(activo=True).count(),
        "inscripciones": Inscripcion.objects.count(),
        "aprobados": Inscripcion.objects.filter(estado=APROBADO).count(),
        "faltas": Inscripcion.objects.filter(estado=FALTO).count(),
        "certificados": Certificado.objects.count(),
        "cursos_detalle": CursoSerializer(cursos, many=True).data,
    })
