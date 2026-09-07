"""Capa de datos (SQLite) del sistema de gestión de cursos."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Any, Iterable

APP_DIR = os.path.join(os.path.expanduser("~"), ".gestion_curso")
DB_PATH = os.path.join(APP_DIR, "gestion_curso.db")
CERT_DIR = os.path.join(APP_DIR, "certificados")

SCHEMA = """
CREATE TABLE IF NOT EXISTS personas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    cedula       TEXT UNIQUE,
    nombres      TEXT NOT NULL,
    apellidos    TEXT NOT NULL,
    email        TEXT,
    telefono     TEXT,
    creado_en    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cursos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL UNIQUE,
    codigo       TEXT,
    instructor   TEXT,
    fecha_inicio TEXT,
    fecha_fin    TEXT,
    horas        INTEGER,
    creado_en    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inscripciones (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    persona_id   INTEGER NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    curso_id     INTEGER NOT NULL REFERENCES cursos(id)   ON DELETE CASCADE,
    estado       TEXT NOT NULL DEFAULT 'Inscrito',   -- Aprobado | Reprobado | Faltó | Inscrito
    nota         REAL,
    asistencia   REAL,
    observacion  TEXT,
    actualizado  TEXT NOT NULL,
    UNIQUE(persona_id, curso_id)
);

CREATE TABLE IF NOT EXISTS certificados (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    inscripcion_id INTEGER NOT NULL REFERENCES inscripciones(id) ON DELETE CASCADE,
    archivo        TEXT NOT NULL,
    nombre_archivo TEXT NOT NULL,
    curso_detectado   TEXT,
    persona_detectada TEXT,
    cargado_en     TEXT NOT NULL
);
"""

ESTADOS = ["Inscrito", "Aprobado", "Reprobado", "Faltó"]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Database:
    def __init__(self, path: str = DB_PATH) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        os.makedirs(CERT_DIR, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ---------------------------------------------------------- utilidades
    def q(self, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, tuple(params)).fetchall()

    def x(self, sql: str, params: Iterable[Any] = ()) -> int:
        cur = self.conn.execute(sql, tuple(params))
        self.conn.commit()
        return cur.lastrowid

    # ------------------------------------------------------------ personas
    def upsert_persona(self, cedula, nombres, apellidos, email=None, telefono=None) -> int:
        cedula = (cedula or "").strip() or None
        nombres = (nombres or "").strip()
        apellidos = (apellidos or "").strip()
        if cedula:
            row = self.conn.execute("SELECT id FROM personas WHERE cedula=?", (cedula,)).fetchone()
        else:
            row = self.conn.execute(
                "SELECT id FROM personas WHERE lower(nombres)=lower(?) AND lower(apellidos)=lower(?)",
                (nombres, apellidos),
            ).fetchone()
        if row:
            self.x(
                "UPDATE personas SET nombres=?, apellidos=?, "
                "email=COALESCE(?,email), telefono=COALESCE(?,telefono) WHERE id=?",
                (nombres, apellidos, email, telefono, row["id"]),
            )
            return row["id"]
        return self.x(
            "INSERT INTO personas (cedula,nombres,apellidos,email,telefono,creado_en)"
            " VALUES (?,?,?,?,?,?)",
            (cedula, nombres, apellidos, email, telefono, _now()),
        )

    def personas(self, filtro: str = "") -> list[sqlite3.Row]:
        like = f"%{filtro.strip()}%"
        return self.q(
            """SELECT p.*,
                   (SELECT COUNT(*) FROM inscripciones i WHERE i.persona_id=p.id) AS cursos,
                   (SELECT COUNT(*) FROM inscripciones i WHERE i.persona_id=p.id AND i.estado='Aprobado') AS aprobados
               FROM personas p
               WHERE ? = '' OR p.nombres LIKE ? OR p.apellidos LIKE ? OR IFNULL(p.cedula,'') LIKE ?
               ORDER BY p.apellidos, p.nombres""",
            (filtro.strip(), like, like, like),
        )

    def eliminar_persona(self, persona_id: int) -> None:
        self.x("DELETE FROM personas WHERE id=?", (persona_id,))

    # -------------------------------------------------------------- cursos
    def upsert_curso(self, nombre, codigo=None, instructor=None,
                     fecha_inicio=None, fecha_fin=None, horas=None) -> int:
        nombre = (nombre or "").strip()
        row = self.conn.execute("SELECT id FROM cursos WHERE lower(nombre)=lower(?)", (nombre,)).fetchone()
        if row:
            self.x(
                "UPDATE cursos SET codigo=COALESCE(?,codigo), instructor=COALESCE(?,instructor),"
                " fecha_inicio=COALESCE(?,fecha_inicio), fecha_fin=COALESCE(?,fecha_fin),"
                " horas=COALESCE(?,horas) WHERE id=?",
                (codigo, instructor, fecha_inicio, fecha_fin, horas, row["id"]),
            )
            return row["id"]
        return self.x(
            "INSERT INTO cursos (nombre,codigo,instructor,fecha_inicio,fecha_fin,horas,creado_en)"
            " VALUES (?,?,?,?,?,?,?)",
            (nombre, codigo, instructor, fecha_inicio, fecha_fin, horas, _now()),
        )

    def cursos(self) -> list[sqlite3.Row]:
        return self.q(
            """SELECT c.*,
                   (SELECT COUNT(*) FROM inscripciones i WHERE i.curso_id=c.id) AS participantes,
                   (SELECT COUNT(*) FROM inscripciones i WHERE i.curso_id=c.id AND i.estado='Aprobado') AS aprobados,
                   (SELECT COUNT(*) FROM inscripciones i WHERE i.curso_id=c.id AND i.estado='Faltó') AS faltas
               FROM cursos c ORDER BY c.nombre"""
        )

    def eliminar_curso(self, curso_id: int) -> None:
        self.x("DELETE FROM cursos WHERE id=?", (curso_id,))

    # -------------------------------------------------------- inscripciones
    def upsert_inscripcion(self, persona_id, curso_id, estado="Inscrito",
                           nota=None, asistencia=None, observacion=None) -> int:
        estado = estado if estado in ESTADOS else "Inscrito"
        row = self.conn.execute(
            "SELECT id FROM inscripciones WHERE persona_id=? AND curso_id=?", (persona_id, curso_id)
        ).fetchone()
        if row:
            self.x(
                "UPDATE inscripciones SET estado=?, nota=COALESCE(?,nota),"
                " asistencia=COALESCE(?,asistencia), observacion=COALESCE(?,observacion),"
                " actualizado=? WHERE id=?",
                (estado, nota, asistencia, observacion, _now(), row["id"]),
            )
            return row["id"]
        return self.x(
            "INSERT INTO inscripciones (persona_id,curso_id,estado,nota,asistencia,observacion,actualizado)"
            " VALUES (?,?,?,?,?,?,?)",
            (persona_id, curso_id, estado, nota, asistencia, observacion, _now()),
        )

    def participantes_de_curso(self, curso_id: int) -> list[sqlite3.Row]:
        return self.q(
            """SELECT i.id AS inscripcion_id, p.id AS persona_id, p.cedula, p.nombres, p.apellidos,
                      i.estado, i.nota, i.asistencia,
                      (SELECT COUNT(*) FROM certificados ce WHERE ce.inscripcion_id=i.id) AS certificados
               FROM inscripciones i JOIN personas p ON p.id=i.persona_id
               WHERE i.curso_id=? ORDER BY p.apellidos, p.nombres""",
            (curso_id,),
        )

    def historial_persona(self, persona_id: int) -> list[sqlite3.Row]:
        return self.q(
            """SELECT i.id AS inscripcion_id, c.id AS curso_id, c.nombre AS curso, c.codigo,
                      c.fecha_inicio, c.fecha_fin, c.horas, i.estado, i.nota, i.asistencia, i.observacion,
                      (SELECT COUNT(*) FROM certificados ce WHERE ce.inscripcion_id=i.id) AS certificados
               FROM inscripciones i JOIN cursos c ON c.id=i.curso_id
               WHERE i.persona_id=? ORDER BY c.nombre""",
            (persona_id,),
        )

    def set_estado(self, inscripcion_id: int, estado: str) -> None:
        self.x("UPDATE inscripciones SET estado=?, actualizado=? WHERE id=?",
               (estado, _now(), inscripcion_id))

    # -------------------------------------------------------- certificados
    def guardar_certificado(self, inscripcion_id, ruta, nombre_archivo,
                            curso_detectado=None, persona_detectada=None) -> int:
        return self.x(
            "INSERT INTO certificados (inscripcion_id,archivo,nombre_archivo,"
            "curso_detectado,persona_detectada,cargado_en) VALUES (?,?,?,?,?,?)",
            (inscripcion_id, ruta, nombre_archivo, curso_detectado, persona_detectada, _now()),
        )

    def certificados(self, filtro: str = "") -> list[sqlite3.Row]:
        like = f"%{filtro.strip()}%"
        return self.q(
            """SELECT ce.*, p.nombres, p.apellidos, p.cedula, c.nombre AS curso
               FROM certificados ce
               JOIN inscripciones i ON i.id=ce.inscripcion_id
               JOIN personas p ON p.id=i.persona_id
               JOIN cursos c ON c.id=i.curso_id
               WHERE ? = '' OR p.nombres LIKE ? OR p.apellidos LIKE ? OR c.nombre LIKE ?
               ORDER BY ce.cargado_en DESC""",
            (filtro.strip(), like, like, like),
        )

    def certificados_de_inscripcion(self, inscripcion_id: int) -> list[sqlite3.Row]:
        return self.q("SELECT * FROM certificados WHERE inscripcion_id=?", (inscripcion_id,))

    # ------------------------------------------------------------ métricas
    def resumen(self) -> dict[str, int]:
        g = lambda s: self.conn.execute(s).fetchone()[0]
        return {
            "personas": g("SELECT COUNT(*) FROM personas"),
            "cursos": g("SELECT COUNT(*) FROM cursos"),
            "aprobados": g("SELECT COUNT(*) FROM inscripciones WHERE estado='Aprobado'"),
            "faltas": g("SELECT COUNT(*) FROM inscripciones WHERE estado='Faltó'"),
            "certificados": g("SELECT COUNT(*) FROM certificados"),
        }
