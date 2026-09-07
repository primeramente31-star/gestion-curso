from rest_framework import serializers

from .models import Certificado, Curso, Inscripcion, Participante


class CertificadoSerializer(serializers.ModelSerializer):
    participante = serializers.CharField(source="inscripcion.participante.nombre_completo", read_only=True)
    dni = serializers.CharField(source="inscripcion.participante.dni", read_only=True)
    curso = serializers.CharField(source="inscripcion.curso.nombre", read_only=True)
    archivo_url = serializers.SerializerMethodField()

    class Meta:
        model = Certificado
        fields = ["id", "inscripcion", "participante", "dni", "curso",
                  "archivo_url", "curso_detectado", "participante_detectado", "cargado_en"]
        read_only_fields = ["cargado_en"]

    def get_archivo_url(self, obj):
        # URL relativa a propósito: el frontend se sirve tras un proxy, por lo que
        # una URL absoluta al backend no sería alcanzable desde el navegador.
        return obj.archivo.url if obj.archivo else None


class InscripcionSerializer(serializers.ModelSerializer):
    participante_nombre = serializers.CharField(source="participante.nombre_completo", read_only=True)
    dni = serializers.CharField(source="participante.dni", read_only=True)
    curso_nombre = serializers.CharField(source="curso.nombre", read_only=True)
    certificados = CertificadoSerializer(many=True, read_only=True)
    total_certificados = serializers.IntegerField(source="certificados.count", read_only=True)

    class Meta:
        model = Inscripcion
        fields = ["id", "participante", "participante_nombre", "dni", "curso", "curso_nombre",
                  "estado", "nota", "asistencia", "observacion", "actualizado_en",
                  "certificados", "total_certificados"]


class CursoSerializer(serializers.ModelSerializer):
    total_participantes = serializers.IntegerField(read_only=True)
    total_aprobados = serializers.IntegerField(read_only=True)
    total_faltas = serializers.IntegerField(read_only=True)
    porcentaje_aprobacion = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = ["id", "nombre", "codigo", "instructor", "fecha_inicio", "fecha_fin",
                  "horas", "activo", "creado_en", "total_participantes",
                  "total_aprobados", "total_faltas", "porcentaje_aprobacion"]

    def get_porcentaje_aprobacion(self, obj):
        total = getattr(obj, "total_participantes", None)
        if not total:
            return 0
        return round(getattr(obj, "total_aprobados", 0) / total * 100, 1)


class ParticipanteSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(read_only=True)
    total_cursos = serializers.IntegerField(read_only=True)
    total_aprobados = serializers.IntegerField(read_only=True)
    total_faltas = serializers.IntegerField(read_only=True)

    class Meta:
        model = Participante
        fields = ["id", "dni", "nombres", "apellidos", "nombre_completo", "email",
                  "telefono", "creado_en", "total_cursos", "total_aprobados", "total_faltas"]


class ReporteParticipanteSerializer(serializers.ModelSerializer):
    """Reporte detallado: cursos realizados, faltas, aprobados y certificados."""
    nombre_completo = serializers.CharField(read_only=True)
    resumen = serializers.SerializerMethodField()
    cursos = serializers.SerializerMethodField()

    class Meta:
        model = Participante
        fields = ["id", "dni", "nombres", "apellidos", "nombre_completo",
                  "email", "telefono", "resumen", "cursos"]

    def get_resumen(self, obj):
        ins = list(obj.inscripciones.all())
        return {
            "total_cursos": len(ins),
            "aprobados": sum(1 for i in ins if i.estado == Inscripcion.Estado.APROBADO),
            "reprobados": sum(1 for i in ins if i.estado == Inscripcion.Estado.REPROBADO),
            "faltas": sum(1 for i in ins if i.estado == Inscripcion.Estado.FALTO),
            "certificados": sum(i.certificados.count() for i in ins),
        }

    def get_cursos(self, obj):
        return InscripcionSerializer(
            obj.inscripciones.select_related("curso").prefetch_related("certificados"),
            many=True, context=self.context).data


class ImportacionSerializer(serializers.Serializer):
    archivo = serializers.FileField()
    curso_por_defecto = serializers.CharField(required=False, allow_blank=True)


class CargaCertificadoSerializer(serializers.Serializer):
    archivo = serializers.FileField()
    aprobar = serializers.BooleanField(default=True)
