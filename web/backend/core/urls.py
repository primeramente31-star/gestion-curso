from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("participantes", views.ParticipanteViewSet, basename="participante")
router.register("cursos", views.CursoViewSet, basename="curso")
router.register("inscripciones", views.InscripcionViewSet, basename="inscripcion")
router.register("certificados", views.CertificadoViewSet, basename="certificado")

urlpatterns = [
    path("", include(router.urls)),
    path("importar-excel/", views.importar_excel, name="importar-excel"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
