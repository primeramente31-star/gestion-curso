"""Lectura de certificados elaborados por un externo.

El sistema extrae del archivo (PDF o nombre de archivo) el CURSO y el
NOMBRE/APELLIDO del participante, y lo vincula con la inscripción correspondiente.
"""
from __future__ import annotations

import os
import re
import shutil
import unicodedata
from dataclasses import dataclass, field

from .db import CERT_DIR, Database


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t.lower()).strip()


def extraer_texto(ruta: str) -> str:
    """Texto del PDF; si no es PDF o falla, usa el nombre del archivo."""
    base = os.path.splitext(os.path.basename(ruta))[0].replace("_", " ").replace("-", " ")
    if ruta.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(ruta)
            texto = "\n".join((p.extract_text() or "") for p in reader.pages[:3])
            if texto.strip():
                return texto + "\n" + base
        except Exception:  # noqa: BLE001
            pass
    return base


def detectar_curso(texto: str, cursos: list[str]) -> str | None:
    """El curso cuyo nombre aparezca en el texto (coincidencia más larga)."""
    t = _norm(texto)
    candidatos = [c for c in cursos if _norm(c) and _norm(c) in t]
    if candidatos:
        return max(candidatos, key=lambda c: len(c))
    # fallback: mayor solapamiento de palabras significativas
    mejor, puntaje = None, 0.0
    palabras = set(t.split())
    for c in cursos:
        pc = {w for w in _norm(c).split() if len(w) > 3}
        if not pc:
            continue
        score = len(pc & palabras) / len(pc)
        if score > puntaje:
            mejor, puntaje = c, score
    return mejor if puntaje >= 0.6 else None


def detectar_persona(texto: str, personas: list[tuple[int, str, str, str | None]]):
    """personas: (id, nombres, apellidos, cedula). Devuelve (id, etiqueta) o None."""
    t = _norm(texto)
    for pid, nombres, apellidos, cedula in personas:
        if cedula and _norm(cedula) and _norm(cedula) in t:
            return pid, f"{nombres} {apellidos}"
    mejor, puntaje, etiqueta = None, 0.0, ""
    for pid, nombres, apellidos, _ in personas:
        tokens = {w for w in _norm(f"{nombres} {apellidos}").split() if len(w) > 2}
        if not tokens:
            continue
        score = len(tokens & set(t.split())) / len(tokens)
        if score > puntaje:
            mejor, puntaje, etiqueta = pid, score, f"{nombres} {apellidos}"
    return (mejor, etiqueta) if puntaje >= 0.6 else None


@dataclass
class Deteccion:
    archivo: str
    curso: str | None = None
    persona: str | None = None
    persona_id: int | None = None
    curso_id: int | None = None
    inscripcion_id: int | None = None
    estado: str = ""
    mensaje: str = ""

    @property
    def ok(self) -> bool:
        return self.inscripcion_id is not None


@dataclass
class ResultadoCarga:
    guardados: int = 0
    detecciones: list[Deteccion] = field(default_factory=list)


def analizar(db: Database, ruta: str) -> Deteccion:
    texto = extraer_texto(ruta)
    d = Deteccion(archivo=ruta)

    cursos = {r["nombre"]: r["id"] for r in db.q("SELECT id, nombre FROM cursos")}
    nombre_curso = detectar_curso(texto, list(cursos))
    if nombre_curso:
        d.curso, d.curso_id = nombre_curso, cursos[nombre_curso]

    personas = [(r["id"], r["nombres"], r["apellidos"], r["cedula"])
                for r in db.q("SELECT id,nombres,apellidos,cedula FROM personas")]
    hallada = detectar_persona(texto, personas)
    if hallada:
        d.persona_id, d.persona = hallada

    if not d.curso_id:
        d.mensaje = "No se identificó el curso en el certificado."
        return d
    if not d.persona_id:
        d.mensaje = "No se identificó al participante en el certificado."
        return d

    row = db.q("SELECT id, estado FROM inscripciones WHERE persona_id=? AND curso_id=?",
               (d.persona_id, d.curso_id))
    if not row:
        d.mensaje = "El participante no está inscrito en ese curso."
        return d
    d.inscripcion_id, d.estado = row[0]["id"], row[0]["estado"]
    if d.estado != "Aprobado":
        d.mensaje = f"Detectado, pero el estado actual es '{d.estado}' (se puede marcar como Aprobado al guardar)."
    else:
        d.mensaje = "Listo para guardar."
    return d


def guardar(db: Database, d: Deteccion, aprobar: bool = True) -> str:
    """Copia el certificado al almacén interno y lo registra."""
    if not d.inscripcion_id:
        raise ValueError("Detección incompleta.")
    if aprobar and d.estado != "Aprobado":
        db.set_estado(d.inscripcion_id, "Aprobado")

    os.makedirs(CERT_DIR, exist_ok=True)
    base = re.sub(r"[^\w.\- ]", "_", os.path.basename(d.archivo))
    destino = os.path.join(CERT_DIR, f"{d.inscripcion_id}_{base}")
    n = 1
    while os.path.exists(destino):
        raiz, ext = os.path.splitext(base)
        destino = os.path.join(CERT_DIR, f"{d.inscripcion_id}_{raiz}({n}){ext}")
        n += 1
    shutil.copy2(d.archivo, destino)
    db.guardar_certificado(d.inscripcion_id, destino, os.path.basename(destino), d.curso, d.persona)
    return destino
