# Sistema de Gestión de Cursos

Aplicación **de escritorio** (Python + PySide6) para administrar las personas que han
participado en los cursos de la organización.

## Funcionalidades

| # | Requerimiento | Implementación |
|---|---------------|----------------|
| 1 | Gestión de personas por curso | Módulos *Participantes* y *Cursos* con base de datos SQLite local |
| 2 | Carga desde Excel | *Importar Excel* — lee `.xlsx`, `.xls` y `.csv`, detecta las columnas automáticamente |
| 3 | Organización por curso | Pantalla *Cursos*: selector de curso + listado de sus participantes y estados |
| 4 | Software de escritorio | Aplicación nativa PySide6 (Windows, macOS, Linux); datos en `~/.gestion_curso` |
| 5 | Reporte por persona | *Reportes*: cursos realizados, aprobados, reprobados, faltas, notas y certificados. Exportable a PDF |
| 6 | Resguardo de certificados | *Certificados*: lee el PDF (o el nombre del archivo), detecta **curso** y **nombres/apellidos**, lo vincula al participante aprobado y archiva una copia |

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Importación de Excel

Los encabezados se reconocen sin distinguir mayúsculas ni acentos. Columnas soportadas:

`Cédula` · `Nombres` · `Apellidos` (o `Nombre completo`) · `Email` · `Teléfono` ·
**`Curso`** · `Código` · `Instructor` · `Fecha inicio` · `Fecha fin` · `Horas` ·
`Estado` · `Nota` · `Asistencia` · `Observación`

- La única columna imprescindible es el nombre/apellido; si el archivo no trae `Curso`,
  la app pide el nombre del curso y lo aplica a todas las filas.
- El `Estado` se normaliza a **Aprobado / Reprobado / Faltó / Inscrito**
  (acepta variantes como *aprobado, si, falto, ausente, reprobado…*).
- Reimportar el mismo archivo **actualiza** en lugar de duplicar (clave: cédula, o nombre+apellido).
- El botón *Descargar plantilla* genera un Excel de ejemplo con todas las columnas.

## Certificados

Los certificados los elabora un externo. Al cargarlos, el sistema:

1. Extrae el texto del PDF (si falla, usa el nombre del archivo).
2. Detecta el **curso** comparándolo con los cursos registrados.
3. Detecta al **participante** por cédula o por coincidencia de nombres y apellidos.
4. Verifica que exista la inscripción, marca al participante como **Aprobado** y archiva
   una copia en `~/.gestion_curso/certificados`.

Los archivos que no se puedan identificar se reportan indicando el motivo.

## Estructura

```
main.py                 Punto de entrada
app/db.py               Modelo de datos SQLite
app/importer.py         Importación y normalización de Excel/CSV
app/certificados.py     Lectura y vinculación de certificados
app/reportes.py         Reporte del participante (HTML/PDF) y CSV por curso
app/main_window.py      Interfaz principal
app/widgets.py          Componentes reutilizables
app/theme.py            Tema visual (colores y estilos centralizados)
docs/capturas/          Capturas de la interfaz
```

## Generar el ejecutable (.exe)

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "GestionCursos" main.py
```
