"""Lógica de negocio: importación de Excel y lectura de certificados."""
from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass, field

import pandas as pd
from django.db import transaction

from .models import Certificado, Curso, Inscripcion, Participante

# --------------------------------------------------------------------- utils
ALIAS: dict[str, list[str]] = {
    "dni": ["dni", "cedula", "ci", "documento", "identificacion", "nrodocumento", "rut"],
    "nombres": ["nombres", "nombre", "firstname", "primernombre"],
    "apellidos": ["apellidos", "apellido", "lastname", "primerapellido"],
    "nombre_completo": ["nombrecompleto", "participante", "nombreyapellido", "fullname",
                        "nombresyapellidos"],
    "email": ["email", "correo", "correoelectronico", "mail"],
    "telefono": ["telefono", "tlf", "celular", "movil", "phone"],
    "curso": ["curso", "nombrecurso", "capacitacion", "taller", "programa"],
    "codigo": ["codigo", "codigocurso", "cod"],
    "instructor": ["instructor", "facilitador", "docente", "profesor"],
    "fecha_inicio": ["fechainicio", "inicio", "desde"],
    "fecha_fin": ["fechafin", "fin", "hasta"],
    "horas": ["horas", "duracion", "horasacademicas"],
    "estado": ["estado", "condicion", "resultado", "status"],
    "nota": ["nota", "calificacion", "puntaje", "score"],
    "asistencia": ["asistencia", "porcentajeasistencia", "%asistencia"],
    "observacion": ["observacion", "observaciones", "comentario"],
}


def norm(text) -> str:
    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return "".join(c for c in t.lower() if c.isalnum() or c == "%")


def norm_espacios(text) -> str:
    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t.lower()).strip()


def mapear_columnas(columnas) -> dict[str, str]:
    normalizadas = {norm(c): c for c in columnas}
    mapa = {}
    for campo, alias in ALIAS.items():
        for a in alias:
            if a in normalizadas:
                mapa[campo] = normalizadas[a]
                break
    return mapa


def normalizar_estado(valor) -> str:
    v = norm(valor or "")
    if not v:
        return Inscripcion.Estado.INSCRITO
    if v.startswith("aprob") or v in {"a", "si", "p", "pass"}:
        return Inscripcion.Estado.APROBADO
    if v.startswith("reprob") or v in {"r", "no", "fail"}:
        return Inscripcion.Estado.REPROBADO
    if v.startswith("falt") or v in {"f", "ausente", "inasistente", "nsp"}:
        return Inscripcion.Estado.FALTO
    for e in Inscripcion.Estado.values:
        if norm(e) == v:
            return e
    return Inscripcion.Estado.INSCRITO


def _txt(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return str(v).strip() or None


def _num(v):
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        return float(str(v).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _fecha(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return pd.to_datetime(v).date()
    except Exception:
        return None


def partir_nombre(completo: str) -> tuple[str, str]:
    partes = [p for p in str(completo).replace(",", " ").split() if p]
    if not partes:
        return "", ""
    if len(partes) == 1:
        return partes[0], ""
    if len(partes) == 2:
        return partes[0], partes[1]
    m = len(partes) // 2
    return " ".join(partes[:m]), " ".join(partes[m:])


# ---------------------------------------------------------------- importación
@dataclass
class ResultadoImportacion:
    filas: int = 0
    participantes_nuevos: int = 0
    cursos_nuevos: int = 0
    inscripciones: int = 0
    columnas_detectadas: dict = field(default_factory=dict)
    errores: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "filas_procesadas": self.filas,
            "participantes_nuevos": self.participantes_nuevos,
            "cursos_nuevos": self.cursos_nuevos,
            "inscripciones": self.inscripciones,
            "columnas_detectadas": self.columnas_detectadas,
            "errores": self.errores[:50],
            "total_errores": len(self.errores),
        }


def leer_dataframe(archivo, nombre: str = "") -> pd.DataFrame:
    nombre = (nombre or getattr(archivo, "name", "")).lower()
    if nombre.endswith(".csv"):
        return pd.read_csv(archivo, dtype=object, keep_default_na=False, na_values=[""])
    return pd.read_excel(archivo, dtype=object)


@transaction.atomic
def importar_dataframe(df: pd.DataFrame, curso_por_defecto: str | None = None) -> ResultadoImportacion:
    res = ResultadoImportacion()
    mapa = mapear_columnas(list(df.columns))
    res.columnas_detectadas = mapa

    if "curso" not in mapa and not curso_por_defecto:
        res.errores.append("No se encontró la columna 'Curso' ni se indicó un curso por defecto.")
        return res

    get = lambda fila, campo: fila.get(mapa[campo]) if campo in mapa else None

    for idx, fila in df.iterrows():
        fila = fila.to_dict()
        try:
            nombres = _txt(get(fila, "nombres"))
            apellidos = _txt(get(fila, "apellidos"))
            if not nombres and not apellidos:
                completo = _txt(get(fila, "nombre_completo"))
                if not completo:
                    continue
                nombres, apellidos = partir_nombre(completo)
            if not (nombres or apellidos):
                continue

            nombre_curso = _txt(get(fila, "curso")) or curso_por_defecto
            if not nombre_curso:
                res.errores.append(f"Fila {idx + 2}: sin curso.")
                continue

            dni = _txt(get(fila, "dni"))
            defaults = {"nombres": nombres or "", "apellidos": apellidos or ""}
            if _txt(get(fila, "email")):
                defaults["email"] = _txt(get(fila, "email"))
            if _txt(get(fila, "telefono")):
                defaults["telefono"] = _txt(get(fila, "telefono"))

            if dni:
                participante, nuevo_p = Participante.objects.update_or_create(
                    dni=dni, defaults=defaults)
            else:
                participante, nuevo_p = Participante.objects.get_or_create(
                    nombres__iexact=nombres or "", apellidos__iexact=apellidos or "",
                    defaults=defaults)

            curso_defaults = {k: v for k, v in {
                "codigo": _txt(get(fila, "codigo")),
                "instructor": _txt(get(fila, "instructor")),
                "fecha_inicio": _fecha(get(fila, "fecha_inicio")),
                "fecha_fin": _fecha(get(fila, "fecha_fin")),
                "horas": int(_num(get(fila, "horas"))) if _num(get(fila, "horas")) else None,
            }.items() if v is not None}
            curso, nuevo_c = Curso.objects.get_or_create(
                nombre=nombre_curso, defaults=curso_defaults)
            if not nuevo_c and curso_defaults:
                for k, v in curso_defaults.items():
                    setattr(curso, k, v)
                curso.save()

            insc_defaults = {"estado": normalizar_estado(get(fila, "estado"))}
            for k, v in {"nota": _num(get(fila, "nota")),
                         "asistencia": _num(get(fila, "asistencia")),
                         "observacion": _txt(get(fila, "observacion"))}.items():
                if v is not None:
                    insc_defaults[k] = v
            Inscripcion.objects.update_or_create(
                participante=participante, curso=curso, defaults=insc_defaults)

            res.filas += 1
            res.inscripciones += 1
            res.participantes_nuevos += int(nuevo_p)
            res.cursos_nuevos += int(nuevo_c)
        except Exception as exc:  # noqa: BLE001
            res.errores.append(f"Fila {idx + 2}: {exc}")
    return res


# --------------------------------------------------------------- certificados
def extraer_texto(ruta: str) -> str:
    base = os.path.splitext(os.path.basename(ruta))[0].replace("_", " ").replace("-", " ")
    if ruta.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader

            texto = "\n".join((p.extract_text() or "") for p in PdfReader(ruta).pages[:3])
            if texto.strip():
                return texto + "\n" + base
        except Exception:  # noqa: BLE001
            pass
    return base


def detectar_curso(texto: str):
    t = norm_espacios(texto)
    cursos = list(Curso.objects.all())
    coincidencias = [c for c in cursos if norm_espacios(c.nombre) and norm_espacios(c.nombre) in t]
    if coincidencias:
        return max(coincidencias, key=lambda c: len(c.nombre))
    mejor, puntaje = None, 0.0
    palabras = set(t.split())
    for c in cursos:
        tokens = {w for w in norm_espacios(c.nombre).split() if len(w) > 3}
        if not tokens:
            continue
        score = len(tokens & palabras) / len(tokens)
        if score > puntaje:
            mejor, puntaje = c, score
    return mejor if puntaje >= 0.6 else None


def detectar_participante(texto: str):
    t = norm_espacios(texto)
    personas = list(Participante.objects.all())
    for p in personas:
        if p.dni and norm_espacios(p.dni) and norm_espacios(p.dni) in t:
            return p
    mejor, puntaje = None, 0.0
    palabras = set(t.split())
    for p in personas:
        tokens = {w for w in norm_espacios(p.nombre_completo).split() if len(w) > 2}
        if not tokens:
            continue
        score = len(tokens & palabras) / len(tokens)
        if score > puntaje:
            mejor, puntaje = p, score
    return mejor if puntaje >= 0.6 else None


@dataclass
class DeteccionCertificado:
    curso: Curso | None = None
    participante: Participante | None = None
    inscripcion: Inscripcion | None = None
    mensaje: str = ""

    @property
    def ok(self) -> bool:
        return self.inscripcion is not None


def analizar_certificado(ruta: str) -> DeteccionCertificado:
    texto = extraer_texto(ruta)
    d = DeteccionCertificado()
    d.curso = detectar_curso(texto)
    d.participante = detectar_participante(texto)

    if not d.curso:
        d.mensaje = "No se identificó el curso en el certificado."
        return d
    if not d.participante:
        d.mensaje = "No se identificó al participante en el certificado."
        return d
    d.inscripcion = Inscripcion.objects.filter(
        participante=d.participante, curso=d.curso).first()
    if not d.inscripcion:
        d.mensaje = "El participante no está inscrito en ese curso."
    else:
        d.mensaje = "Certificado identificado correctamente."
    return d
