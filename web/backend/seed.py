"""Datos de demostración."""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
import pandas as pd
from core import services
from core.models import Curso

df = pd.DataFrame([
 {"Cédula":"V-18456321","Nombres":"María José","Apellidos":"Pérez Rojas","Email":"maria.perez@correo.com","Curso":"Seguridad Industrial","Código":"SI-01","Instructor":"Ing. López","Fecha Inicio":"2026-01-15","Fecha Fin":"2026-01-20","Horas":16,"Estado":"Aprobado","Nota":18.5,"Asistencia":100},
 {"Cédula":"V-20114785","Nombre Completo":"Carlos Alberto Gómez Ruiz","Email":"cgomez@correo.com","Curso":"Seguridad Industrial","Código":"SI-01","Instructor":"Ing. López","Horas":16,"Estado":"Faltó","Asistencia":20},
 {"Cédula":"V-15987456","Nombres":"Ana Lucía","Apellidos":"Martínez Silva","Curso":"Seguridad Industrial","Código":"SI-01","Horas":16,"Estado":"Aprobado","Nota":16,"Asistencia":92},
 {"Cédula":"V-18456321","Nombres":"María José","Apellidos":"Pérez Rojas","Curso":"Primeros Auxilios","Código":"PA-02","Instructor":"Dra. Ramírez","Fecha Inicio":"2026-03-02","Fecha Fin":"2026-03-05","Horas":8,"Estado":"Aprobado","Nota":19,"Asistencia":100},
 {"Cédula":"V-20114785","Nombres":"Carlos Alberto","Apellidos":"Gómez Ruiz","Curso":"Primeros Auxilios","Código":"PA-02","Horas":8,"Estado":"Reprobado","Nota":9,"Asistencia":75},
 {"Cédula":"V-22334455","Nombres":"Luis Miguel","Apellidos":"Mora Díaz","Curso":"Excel Avanzado","Código":"EX-03","Instructor":"Lic. Torres","Fecha Inicio":"2026-04-10","Horas":24,"Estado":"Inscrito"},
 {"Cédula":"V-15987456","Nombres":"Ana Lucía","Apellidos":"Martínez Silva","Curso":"Excel Avanzado","Código":"EX-03","Horas":24,"Estado":"Inscrito"},
])
r = services.importar_dataframe(df)
print(r.as_dict())
Curso.objects.filter(nombre="Seguridad Industrial").update(activo=False)
print("cursos:", list(Curso.objects.values_list("nombre","activo")))
