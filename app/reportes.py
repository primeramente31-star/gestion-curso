"""Generación del reporte individual de un participante."""
from __future__ import annotations

import csv
import html
from datetime import datetime

from .db import Database

_CSS = """
body{font-family:'Segoe UI',Arial,sans-serif;color:#1f2937;margin:0;padding:24px;}
h1{font-size:20px;margin:0 0 2px;}
.sub{color:#6b7280;font-size:12px;margin-bottom:18px;}
table.cards{border-collapse:separate;border-spacing:8px 0;margin:0 0 16px -8px;width:auto;}
table.cards td{border:1px solid #e5e7eb;border-radius:10px;background:#fafbfc;
  padding:10px 20px;text-align:center;}
table.cards b{font-size:22px;}
table.cards span{font-size:10px;color:#6b7280;text-transform:uppercase;}
table{border-collapse:collapse;width:100%;font-size:12px;}
th{background:#f3f4f6;text-align:left;padding:8px;border-bottom:2px solid #e5e7eb;}
td{padding:8px;border-bottom:1px solid #eef0f3;}
.tag{padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;}
.Aprobado{background:#dcfce7;color:#166534;}
.Reprobado{background:#fee2e2;color:#991b1b;}
.Faltó{background:#fef3c7;color:#92400e;}
.Inscrito{background:#e0e7ff;color:#3730a3;}
.foot{margin-top:20px;color:#9ca3af;font-size:10px;}
"""


def _f(v, alt="—"):
    return html.escape(str(v)) if v not in (None, "", "None") else alt


def reporte_persona_html(db: Database, persona_id: int) -> str:
    p = db.q("SELECT * FROM personas WHERE id=?", (persona_id,))[0]
    hist = db.historial_persona(persona_id)
    tot = len(hist)
    apro = sum(1 for h in hist if h["estado"] == "Aprobado")
    falt = sum(1 for h in hist if h["estado"] == "Faltó")
    repro = sum(1 for h in hist if h["estado"] == "Reprobado")
    certs = sum(h["certificados"] for h in hist)

    filas = "".join(
        f"<tr><td>{_f(h['curso'])}</td><td>{_f(h['codigo'])}</td>"
        f"<td>{_f(h['fecha_inicio'])} — {_f(h['fecha_fin'])}</td>"
        f"<td>{_f(h['horas'])}</td>"
        f"<td><span class='tag {html.escape(h['estado'])}'>{html.escape(h['estado'])}</span></td>"
        f"<td>{_f(h['nota'])}</td><td>{_f(h['asistencia'])}</td>"
        f"<td>{'Sí (%d)' % h['certificados'] if h['certificados'] else 'No'}</td></tr>"
        for h in hist
    ) or "<tr><td colspan='8'>Sin cursos registrados.</td></tr>"

    return f"""<html><head><meta charset='utf-8'><style>{_CSS}</style></head><body>
<h1>Reporte del participante</h1>
<div class='sub'>{_f(p['apellidos'])}, {_f(p['nombres'])} &nbsp;|&nbsp; Cédula: {_f(p['cedula'])}
 &nbsp;|&nbsp; {_f(p['email'])} &nbsp;|&nbsp; {_f(p['telefono'])}</div>
<table class='cards'><tr>
 <td><b>{tot}</b><br><span>Cursos realizados</span></td>
 <td><b>{apro}</b><br><span>Aprobados</span></td>
 <td><b>{repro}</b><br><span>Reprobados</span></td>
 <td><b>{falt}</b><br><span>Faltas</span></td>
 <td><b>{certs}</b><br><span>Certificados</span></td>
</tr></table>
<table><thead><tr><th>Curso</th><th>Código</th><th>Periodo</th><th>Horas</th>
<th>Estado</th><th>Nota</th><th>Asistencia</th><th>Certificado</th></tr></thead>
<tbody>{filas}</tbody></table>
<div class='foot'>Generado el {datetime.now():%d/%m/%Y %H:%M} — Sistema de Gestión de Cursos</div>
</body></html>"""


def exportar_pdf(html_text: str, ruta: str) -> None:
    from PySide6.QtGui import QPageLayout, QPageSize, QTextDocument
    from PySide6.QtCore import QMarginsF
    from PySide6.QtPrintSupport import QPrinter

    doc = QTextDocument()
    doc.setHtml(html_text)
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(ruta)
    printer.setPageLayout(QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Landscape,
                                      QMarginsF(12, 12, 12, 12), QPageLayout.Millimeter))
    doc.print_(printer)


def exportar_csv_curso(db: Database, curso_id: int, ruta: str) -> None:
    filas = db.participantes_de_curso(curso_id)
    with open(ruta, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["Cédula", "Nombres", "Apellidos", "Estado", "Nota", "Asistencia", "Certificados"])
        for f in filas:
            w.writerow([f["cedula"] or "", f["nombres"], f["apellidos"], f["estado"],
                        f["nota"] or "", f["asistencia"] or "", f["certificados"]])
