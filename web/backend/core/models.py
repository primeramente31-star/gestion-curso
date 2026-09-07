"""Modelos del sistema de gestión de participantes."""
from django.db import models


class Participante(models.Model):
    dni = models.CharField("DNI/Cédula", max_length=32, unique=True, null=True, blank=True)
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=40, blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["apellidos", "nombres"]
        indexes = [models.Index(fields=["apellidos", "nombres"])]

    def __str__(self) -> str:
        return f"{self.apellidos}, {self.nombres}"

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}".strip()


class Curso(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    codigo = models.CharField(max_length=40, blank=True, null=True)
    instructor = models.CharField(max_length=120, blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    horas = models.PositiveIntegerField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    participantes = models.ManyToManyField(
        Participante, through="Inscripcion", related_name="cursos")

    class Meta:
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre


class Inscripcion(models.Model):
    class Estado(models.TextChoices):
        INSCRITO = "Inscrito", "Inscrito"
        APROBADO = "Aprobado", "Aprobado"
        REPROBADO = "Reprobado", "Reprobado"
        FALTO = "Faltó", "Faltó"

    participante = models.ForeignKey(
        Participante, on_delete=models.CASCADE, related_name="inscripciones")
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="inscripciones")
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.INSCRITO)
    nota = models.FloatField(blank=True, null=True)
    asistencia = models.FloatField(blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("participante", "curso")
        ordering = ["curso__nombre"]

    def __str__(self) -> str:
        return f"{self.participante} — {self.curso} ({self.estado})"

    @property
    def aprobado(self) -> bool:
        return self.estado == self.Estado.APROBADO


class Certificado(models.Model):
    inscripcion = models.ForeignKey(
        Inscripcion, on_delete=models.CASCADE, related_name="certificados")
    archivo = models.FileField(upload_to="certificados/")
    curso_detectado = models.CharField(max_length=200, blank=True, null=True)
    participante_detectado = models.CharField(max_length=240, blank=True, null=True)
    cargado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-cargado_en"]

    def __str__(self) -> str:
        return f"Certificado {self.inscripcion}"
