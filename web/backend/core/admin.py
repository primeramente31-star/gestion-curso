from django.contrib import admin

from .models import Certificado, Curso, Inscripcion, Participante


@admin.register(Participante)
class ParticipanteAdmin(admin.ModelAdmin):
    list_display = ("apellidos", "nombres", "dni", "email")
    search_fields = ("nombres", "apellidos", "dni")


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "instructor", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "codigo")


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ("participante", "curso", "estado", "nota")
    list_filter = ("estado", "curso")


@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ("inscripcion", "cargado_en")
