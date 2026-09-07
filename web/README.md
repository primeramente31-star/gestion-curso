# Sistema de Gestión de Participantes (Django + React)

Versión **web** del sistema, con API REST en Django y panel de gestión en React.
La versión de escritorio (PySide6) sigue disponible en la raíz del repositorio.

## Arquitectura

```
web/
├── backend/            API REST (Django 5 + Django REST Framework)
│   ├── config/         Configuración del proyecto
│   ├── core/
│   │   ├── models.py       Participante, Curso, Inscripción, Certificado
│   │   ├── serializers.py  Serializadores de la API
│   │   ├── services.py     Importación de Excel y lectura de certificados
│   │   ├── views.py        ViewSets y endpoints
│   │   └── tests.py        24 pruebas (unitarias + integración)
│   ├── Dockerfile
│   └── Procfile
└── frontend/           Panel de gestión (React 19 + Vite)
    └── src/
        ├── api.js          Cliente REST
        ├── components.jsx  Componentes reutilizables
        ├── icons.jsx       Iconos SVG en línea (sin dependencias)
        ├── index.css       Tema visual (variables CSS)
        ├── pages/          Inicio, Participantes, Cursos, Importar,
        │                   Certificados, Reportes, Configuración
        └── *.test.jsx      11 pruebas de interfaz
```

### Modelo de datos

- **Participante** — DNI (único), nombres, apellidos, email, teléfono.
- **Curso** — nombre (único), código, instructor, fechas, horas, `activo`.
- **Inscripción** — relaciona participante ↔ curso (única por par) con estado
  (*Inscrito / Aprobado / Reprobado / Faltó*), nota, asistencia y observación.
- **Certificado** — pertenece a una inscripción; guarda el archivo y los datos detectados.

## Puesta en marcha

```bash
# 1) Backend
cd web/backend
python -m venv ../../.venv && source ../../.venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# 2) Frontend (otra terminal)
cd web/frontend
npm install
npm run dev          # http://localhost:5173
```

El servidor de desarrollo de Vite hace de proxy de `/api` y `/media` hacia Django,
por lo que el frontend siempre usa **rutas relativas**.

Para cargar datos de ejemplo: `python seed.py`.

## Endpoints de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/dashboard/` | Métricas globales y desempeño por curso |
| `GET/POST` | `/api/participantes/` | Listar (con `?search=`) y registrar participantes |
| `GET/PATCH/DELETE` | `/api/participantes/{id}/` | Consultar, actualizar y eliminar |
| `GET` | `/api/participantes/{id}/reporte/` | **Reporte detallado**: cursos, faltas, aprobados y certificados |
| `GET/POST` | `/api/cursos/` | Listar (`?search=`, `?activo=true`) y crear cursos |
| `GET` | `/api/cursos/{id}/participantes/` | Participantes inscritos en un curso |
| `GET/PATCH` | `/api/inscripciones/` | Consultar y actualizar estados (`?curso=`, `?estado=`) |
| `GET` | `/api/certificados/` | Listar certificados (`?search=`) |
| `POST` | `/api/certificados/cargar/` | Sube un certificado, **detecta curso y participante** y lo vincula |
| `POST` | `/api/importar-excel/` | Carga masiva desde `.xlsx`, `.xls` o `.csv` |

La búsqueda de participantes **ignora acentos y mayúsculas** (`Perez` encuentra `Pérez`).

## Importación de Excel

Los encabezados se reconocen automáticamente, sin distinguir acentos ni mayúsculas:

`DNI/Cédula` · `Nombres` · `Apellidos` (o `Nombre completo`) · `Email` · `Teléfono` ·
**`Curso`** · `Código` · `Instructor` · `Fecha inicio` · `Fecha fin` · `Horas` ·
`Estado` · `Nota` · `Asistencia` · `Observación`

- Si el archivo no trae columna `Curso`, se envía `curso_por_defecto`.
- El estado se normaliza (`aprobado`, `sí`, `falto`, `ausente`, `reprobado`…).
- Reimportar **actualiza** en lugar de duplicar (clave: DNI, o nombres + apellidos).
- La importación es **atómica**: si algo falla a mitad, no quedan datos parciales.

## Certificados

Los elabora un proveedor externo. Al subirlos, el sistema:

1. Extrae el texto del PDF (si no tiene texto, usa el nombre del archivo).
2. Detecta el **curso** contra los cursos registrados.
3. Detecta al **participante** por DNI o por nombres y apellidos.
4. Verifica la inscripción, marca **Aprobado** y guarda el archivo.

Si no logra identificarlo responde `422` explicando el motivo, sin guardar nada.

## Pruebas

```bash
cd web/backend  && python manage.py test   # 24 pruebas
cd web/frontend && npm test                # 11 pruebas
```

Cubren: normalización de estados y columnas, importación y reimportación,
detección de certificados, búsquedas, filtro de cursos activos, reporte del
participante, los flujos de la interfaz y que la pantalla de Inicio reproduzca
la estructura del diseño de referencia.

## Interfaz

La pantalla de **Inicio** sigue el diseño acordado: menú lateral azul marino con
iconos, cuatro tarjetas de resumen en color (participantes, cursos activos,
aprobados y certificados), carga de Excel con zona de arrastre, buscador de
cursos y ficha del participante con cursos realizados, faltas, estado y
certificados enlazados.

Todo el estilo está centralizado en variables CSS al inicio de
`frontend/src/index.css`, por lo que colores y tipografía se ajustan sin tocar
la lógica.

## Despliegue

Variables de entorno:

| Variable | Descripción |
|----------|-------------|
| `SECRET_KEY` | Clave secreta de Django (obligatoria en producción) |
| `DEBUG` | `0` en producción |
| `ALLOWED_HOSTS` | Dominios separados por coma |
| `DATABASE_URL` | Cadena de PostgreSQL (si no, usa SQLite) |
| `CSRF_TRUSTED_ORIGINS` | Orígenes con esquema, separados por coma |

Con `DEBUG=0` se activan HTTPS obligatorio, HSTS y cookies seguras.
Los estáticos se sirven con WhiteNoise.

```bash
# Heroku
heroku create && heroku addons:create heroku-postgresql:essential-0
heroku config:set SECRET_KEY="$(openssl rand -base64 48)" DEBUG=0
git push heroku main

# Docker / AWS
cd web && docker compose up --build
```

Para el frontend: `npm run build` genera `dist/`, publicable en cualquier CDN
(S3 + CloudFront, Netlify, Vercel) apuntando `/api` al backend.
