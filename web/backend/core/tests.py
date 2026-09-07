"""Pruebas unitarias y de integración del backend."""
import io
import os
import shutil
import tempfile

import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from . import services
from .models import Certificado, Curso, Inscripcion, Participante

MEDIA_TMP = tempfile.mkdtemp()


def excel_bytes(filas) -> bytes:
    buf = io.BytesIO()
    pd.DataFrame(filas).to_excel(buf, index=False)
    return buf.getvalue()


# ------------------------------------------------------------------ unitarias
class ServiciosTest(TestCase):
    def test_normalizar_estado(self):
        self.assertEqual(services.normalizar_estado("aprobado"), "Aprobado")
        self.assertEqual(services.normalizar_estado("APROBÓ"), "Aprobado")
        self.assertEqual(services.normalizar_estado("falto"), "Faltó")
        self.assertEqual(services.normalizar_estado("ausente"), "Faltó")
        self.assertEqual(services.normalizar_estado("reprobado"), "Reprobado")
        self.assertEqual(services.normalizar_estado(""), "Inscrito")

    def test_mapear_columnas_ignora_acentos_y_mayusculas(self):
        mapa = services.mapear_columnas(["Cédula", "NOMBRES", "Apellidos", "Curso", "Nota"])
        self.assertEqual(mapa["dni"], "Cédula")
        self.assertEqual(mapa["nombres"], "NOMBRES")
        self.assertEqual(mapa["curso"], "Curso")

    def test_partir_nombre(self):
        self.assertEqual(services.partir_nombre("Carlos Gómez"), ("Carlos", "Gómez"))
        self.assertEqual(services.partir_nombre("Carlos Alberto Gómez Ruiz"),
                         ("Carlos Alberto", "Gómez Ruiz"))

    def test_importar_dataframe_crea_registros(self):
        df = pd.DataFrame([
            {"DNI": "V-111", "Nombres": "María", "Apellidos": "Pérez",
             "Curso": "Seguridad Industrial", "Estado": "aprobado", "Nota": 18},
            {"DNI": "V-222", "Nombre Completo": "Carlos Gómez",
             "Curso": "Seguridad Industrial", "Estado": "falto"},
        ])
        res = services.importar_dataframe(df)
        self.assertEqual(res.inscripciones, 2)
        self.assertEqual(Participante.objects.count(), 2)
        self.assertEqual(Curso.objects.count(), 1)
        self.assertEqual(Inscripcion.objects.filter(estado="Aprobado").count(), 1)
        self.assertEqual(Inscripcion.objects.filter(estado="Faltó").count(), 1)

    def test_reimportar_actualiza_sin_duplicar(self):
        df = pd.DataFrame([{"DNI": "V-111", "Nombres": "María", "Apellidos": "Pérez",
                            "Curso": "Excel Avanzado", "Estado": "Inscrito"}])
        services.importar_dataframe(df)
        df.loc[0, "Estado"] = "Aprobado"
        services.importar_dataframe(df)
        self.assertEqual(Participante.objects.count(), 1)
        self.assertEqual(Inscripcion.objects.count(), 1)
        self.assertEqual(Inscripcion.objects.first().estado, "Aprobado")

    def test_importar_sin_columna_curso_usa_defecto(self):
        df = pd.DataFrame([{"Nombres": "Ana", "Apellidos": "Luna"}])
        res = services.importar_dataframe(df, curso_por_defecto="Primeros Auxilios")
        self.assertEqual(res.inscripciones, 1)
        self.assertTrue(Curso.objects.filter(nombre="Primeros Auxilios").exists())

    def test_importar_sin_curso_falla(self):
        res = services.importar_dataframe(pd.DataFrame([{"Nombres": "Ana", "Apellidos": "Luna"}]))
        self.assertEqual(res.inscripciones, 0)
        self.assertTrue(res.errores)


class DeteccionCertificadoTest(TestCase):
    def setUp(self):
        self.curso = Curso.objects.create(nombre="Seguridad Industrial")
        self.persona = Participante.objects.create(
            dni="V-111", nombres="María José", apellidos="Pérez Rojas")
        self.insc = Inscripcion.objects.create(
            participante=self.persona, curso=self.curso, estado="Inscrito")

    def test_detecta_curso_y_participante_desde_texto(self):
        texto = "Certificado otorgado a Maria Jose Perez Rojas por el curso Seguridad Industrial"
        self.assertEqual(services.detectar_curso(texto), self.curso)
        self.assertEqual(services.detectar_participante(texto), self.persona)

    def test_detecta_participante_por_dni(self):
        self.assertEqual(services.detectar_participante("Documento V-111 aprobado"), self.persona)

    def test_no_detecta_persona_desconocida(self):
        self.assertIsNone(services.detectar_participante("Pedro Ramirez Silva"))

    def test_analizar_certificado_por_nombre_de_archivo(self):
        d = tempfile.mkdtemp()
        ruta = os.path.join(d, "Seguridad Industrial - Maria Jose Perez Rojas.pdf")
        open(ruta, "wb").write(b"no-es-un-pdf-valido")
        deteccion = services.analizar_certificado(ruta)
        self.assertTrue(deteccion.ok)
        self.assertEqual(deteccion.inscripcion, self.insc)
        shutil.rmtree(d)


# ---------------------------------------------------------------- integración
@override_settings(MEDIA_ROOT=MEDIA_TMP)
class APITest(APITestCase):
    def setUp(self):
        self.curso = Curso.objects.create(nombre="Seguridad Industrial", activo=True)
        self.inactivo = Curso.objects.create(nombre="Curso Viejo", activo=False)
        self.persona = Participante.objects.create(
            dni="V-111", nombres="María José", apellidos="Pérez Rojas")
        self.insc = Inscripcion.objects.create(
            participante=self.persona, curso=self.curso, estado="Inscrito")

    def test_listar_participantes(self):
        r = self.client.get("/api/participantes/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["total_cursos"], 1)

    def test_buscar_participante(self):
        r = self.client.get("/api/participantes/?search=Perez")
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(self.client.get("/api/participantes/?search=zzz").data["count"], 0)

    def test_crear_participante(self):
        r = self.client.post("/api/participantes/", {
            "dni": "V-999", "nombres": "Ana", "apellidos": "Luna"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Participante.objects.count(), 2)

    def test_filtrar_cursos_activos(self):
        r = self.client.get("/api/cursos/?activo=true")
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["nombre"], "Seguridad Industrial")

    def test_buscar_cursos(self):
        self.assertEqual(self.client.get("/api/cursos/?search=Seguridad").data["count"], 1)

    def test_participantes_de_curso(self):
        r = self.client.get(f"/api/cursos/{self.curso.id}/participantes/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data[0]["participante_nombre"], "María José Pérez Rojas")

    def test_reporte_participante(self):
        r = self.client.get(f"/api/participantes/{self.persona.id}/reporte/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["dni"], "V-111")
        self.assertEqual(r.data["resumen"]["total_cursos"], 1)
        self.assertEqual(r.data["resumen"]["aprobados"], 0)
        self.assertEqual(r.data["cursos"][0]["curso_nombre"], "Seguridad Industrial")

    def test_dashboard(self):
        r = self.client.get("/api/dashboard/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["participantes"], 1)
        self.assertEqual(r.data["cursos_activos"], 1)

    def test_actualizar_estado_inscripcion(self):
        r = self.client.patch(f"/api/inscripciones/{self.insc.id}/",
                              {"estado": "Aprobado"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.insc.refresh_from_db()
        self.assertEqual(self.insc.estado, "Aprobado")

    def test_importar_excel_endpoint(self):
        contenido = excel_bytes([
            {"DNI": "V-777", "Nombres": "Luis", "Apellidos": "Mora",
             "Curso": "Primeros Auxilios", "Estado": "aprobado"}])
        archivo = SimpleUploadedFile(
            "datos.xlsx", contenido,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        r = self.client.post("/api/importar-excel/", {"archivo": archivo}, format="multipart")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["inscripciones"], 1)
        self.assertTrue(Participante.objects.filter(dni="V-777").exists())

    def test_importar_excel_sin_curso_devuelve_error(self):
        archivo = SimpleUploadedFile("d.xlsx", excel_bytes([{"Nombres": "A", "Apellidos": "B"}]))
        r = self.client.post("/api/importar-excel/", {"archivo": archivo}, format="multipart")
        self.assertEqual(r.status_code, 400)

    def test_cargar_certificado_vincula_y_aprueba(self):
        archivo = SimpleUploadedFile(
            "Seguridad Industrial - Maria Jose Perez Rojas.pdf",
            b"contenido", content_type="application/pdf")
        r = self.client.post("/api/certificados/cargar/",
                             {"archivo": archivo, "aprobar": True}, format="multipart")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data["detectado"])
        self.insc.refresh_from_db()
        self.assertEqual(self.insc.estado, "Aprobado")
        self.assertEqual(Certificado.objects.count(), 1)

        rep = self.client.get(f"/api/participantes/{self.persona.id}/reporte/")
        self.assertEqual(rep.data["resumen"]["certificados"], 1)

    def test_cargar_certificado_no_identificado(self):
        archivo = SimpleUploadedFile("documento-cualquiera.pdf", b"x",
                                     content_type="application/pdf")
        r = self.client.post("/api/certificados/cargar/", {"archivo": archivo},
                             format="multipart")
        self.assertEqual(r.status_code, 422)
        self.assertFalse(r.data["detectado"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_TMP, ignore_errors=True)
        super().tearDownClass()
