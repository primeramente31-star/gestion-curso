"""Importación de participantes desde archivos Excel/CSV."""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

import pandas as pd

from .db import Database, ESTADOS

# Sinónimos aceptados por columna lógica
ALIAS: dict[str, list[str]] = {
    "cedula": ["cedula", "ci", "dni", "documento", "identificacion", "nrodocumento", "rut"],
    "nombres": ["nombres", "nombre", "firstname", "primernombre"],
    "apellidos": ["apellidos", "apellido", "lastname", "primerapellido"],
    "nombre_completo": ["nombrecompleto", "participante", "nombreyapellido", "fullname", "nombresyapellidos"],
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
    "observacion": ["observacion", "observaciones", "comentario", "nota_obs"],
}


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return "".join(ch for ch in t.lower() if ch.isalnum() or ch == "%")


def mapear_columnas(columnas: list[str]) -> dict[str, str]:
    """Devuelve {campo_logico: nombre_columna_real}."""
    normalizadas = {_norm(c): c for c in columnas}
    mapa: dict[str, str] = {}
    for campo, alias in ALIAS.items():
        for a in alias:
            if a in normalizadas:
                mapa[campo] = normalizadas[a]
                break
    return mapa


def _normalizar_estado(valor) -> str:
    v = _norm(valor or "")
    if not v:
        return "Inscrito"
    if v.startswith("aprob") or v in {"a", "si", "aprobado", "p", "pass"}:
        return "Aprobado"
    if v.startswith("reprob") or v in {"r", "no", "reprobado", "fail"}:
        return "Reprobado"
    if v.startswith("falt") or v in {"f", "ausente", "inasistente", "nsp"}:
        return "Faltó"
    for e in ESTADOS:
        if _norm(e) == v:
            return e
    return "Inscrito"


def _num(valor):
    try:
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            return None
        return float(str(valor).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _txt(valor):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    s = str(valor).strip()
    return s or None


def _fecha(valor):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    try:
        return pd.to_datetime(valor).date().isoformat()
    except Exception:
        return _txt(valor)


def partir_nombre(completo: str) -> tuple[str, str]:
    partes = [p for p in str(completo).replace(",", " ").split() if p]
    if not partes:
        return "", ""
    if len(partes) == 1:
        return partes[0], ""
    if len(partes) == 2:
        return partes[0], partes[1]
    mitad = len(partes) // 2
    return " ".join(partes[:mitad]), " ".join(partes[mitad:])


@dataclass
class ResultadoImportacion:
    filas: int = 0
    personas_nuevas: int = 0
    cursos_nuevos: int = 0
    inscripciones: int = 0
    errores: list[str] = field(default_factory=list)

    def resumen(self) -> str:
        return (f"Filas procesadas: {self.filas}\n"
                f"Personas nuevas: {self.personas_nuevas}\n"
                f"Cursos nuevos: {self.cursos_nuevos}\n"
                f"Inscripciones registradas: {self.inscripciones}\n"
                f"Errores: {len(self.errores)}")


def leer_archivo(ruta: str, hoja=0) -> pd.DataFrame:
    if ruta.lower().endswith(".csv"):
        return pd.read_csv(ruta, dtype=object, keep_default_na=False, na_values=[""])
    return pd.read_excel(ruta, sheet_name=hoja, dtype=object)


def hojas_de(ruta: str) -> list[str]:
    if ruta.lower().endswith(".csv"):
        return ["CSV"]
    return pd.ExcelFile(ruta).sheet_names


def importar(db: Database, df: pd.DataFrame, curso_por_defecto: str | None = None,
             mapa: dict[str, str] | None = None) -> ResultadoImportacion:
    res = ResultadoImportacion()
    mapa = mapa or mapear_columnas(list(df.columns))
    if "curso" not in mapa and not curso_por_defecto:
        res.errores.append("No se encontró columna 'Curso' y no se indicó un curso por defecto.")
        return res

    personas_previas = {r["id"] for r in db.q("SELECT id FROM personas")}
    cursos_previos = {r["id"] for r in db.q("SELECT id FROM cursos")}
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

            curso_nombre = _txt(get(fila, "curso")) or curso_por_defecto
            if not curso_nombre:
                res.errores.append(f"Fila {idx + 2}: sin curso.")
                continue

            persona_id = db.upsert_persona(
                _txt(get(fila, "cedula")), nombres, apellidos or "",
                _txt(get(fila, "email")), _txt(get(fila, "telefono")))
            curso_id = db.upsert_curso(
                curso_nombre, _txt(get(fila, "codigo")), _txt(get(fila, "instructor")),
                _fecha(get(fila, "fecha_inicio")), _fecha(get(fila, "fecha_fin")),
                _num(get(fila, "horas")))
            db.upsert_inscripcion(
                persona_id, curso_id, _normalizar_estado(get(fila, "estado")),
                _num(get(fila, "nota")), _num(get(fila, "asistencia")),
                _txt(get(fila, "observacion")))

            res.filas += 1
            res.inscripciones += 1
            if persona_id not in personas_previas:
                personas_previas.add(persona_id)
                res.personas_nuevas += 1
            if curso_id not in cursos_previos:
                cursos_previos.add(curso_id)
                res.cursos_nuevos += 1
        except Exception as exc:  # noqa: BLE001
            res.errores.append(f"Fila {idx + 2}: {exc}")
    return res
