"""Ventana principal del Sistema de Gestión de Cursos."""
from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QFileDialog, QHBoxLayout,
                               QInputDialog, QLabel, QLineEdit, QMainWindow,
                               QMessageBox, QPushButton, QStackedWidget,
                               QTextBrowser, QVBoxLayout, QWidget)

from . import certificados as cert_mod
from . import importer, reportes
from .db import CERT_DIR, ESTADOS, Database
from .theme import STYLESHEET
from .widgets import Card, PageHeader, StatCard, Table, row_widget

MENU = [
    ("Panel", "dashboard"),
    ("Participantes", "personas"),
    ("Cursos", "cursos"),
    ("Importar Excel", "importar"),
    ("Certificados", "certificados"),
    ("Reportes", "reportes"),
]


def abrir_archivo(ruta: str) -> None:
    if sys.platform.startswith("win"):
        os.startfile(ruta)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", ruta])
    else:
        QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle("Sistema de Gestión de Cursos")
        self.resize(1240, 780)
        self.setStyleSheet(STYLESHEET)

        central = QWidget()
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._sidebar())

        self.stack = QStackedWidget()
        self.stack.setObjectName("Content")
        for _, key in MENU:
            self.stack.addWidget(getattr(self, f"_page_{key}")())
        lay.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.refrescar_todo()

    # ------------------------------------------------------------ sidebar
    def _sidebar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("Sidebar")
        bar.setFixedWidth(230)
        lay = QVBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 12)
        lay.setSpacing(0)

        logo = QLabel("Gestión de Cursos")
        logo.setObjectName("Logo")
        sub = QLabel("Control de participantes")
        sub.setObjectName("LogoSub")
        lay.addWidget(logo)
        lay.addWidget(sub)

        self.menu_group = QButtonGroup(self)
        self.menu_group.setExclusive(True)
        for i, (texto, _) in enumerate(MENU):
            b = QPushButton(texto)
            b.setCheckable(True)
            b.setChecked(i == 0)
            b.clicked.connect(lambda _c, idx=i: self._ir(idx))
            self.menu_group.addButton(b, i)
            lay.addWidget(b)
        lay.addStretch()
        return bar

    def _ir(self, idx: int) -> None:
        self.stack.setCurrentIndex(idx)
        b = self.menu_group.button(idx)
        if b and not b.isChecked():
            b.setChecked(True)
        self.refrescar_todo()

    @staticmethod
    def _page(titulo: str, subtitulo: str) -> tuple[QWidget, QVBoxLayout, PageHeader]:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)
        header = PageHeader(titulo, subtitulo)
        lay.addWidget(header)
        return w, lay, header

    # ------------------------------------------------------------- panel
    def _page_dashboard(self) -> QWidget:
        w, lay, _ = self._page("Panel general", "Resumen de la actividad formativa")
        self.stats = {k: StatCard(t) for k, t in [
            ("personas", "Participantes"), ("cursos", "Cursos"),
            ("aprobados", "Aprobados"), ("faltas", "Faltas"),
            ("certificados", "Certificados")]}
        lay.addWidget(row_widget(*self.stats.values()))

        c = Card()
        cl = QVBoxLayout(c)
        cl.setContentsMargins(18, 16, 18, 18)
        cl.addWidget(QLabel("<b>Cursos y su desempeño</b>"))
        self.tbl_dash = Table(["Curso", "Código", "Participantes", "Aprobados", "Faltas", "% Aprobación"])
        cl.addWidget(self.tbl_dash)
        lay.addWidget(c, 1)
        return w

    # ------------------------------------------------------ participantes
    def _page_personas(self) -> QWidget:
        w, lay, _ = self._page("Participantes", "Personas registradas en el sistema")
        self.buscar_persona = QLineEdit(placeholderText="Buscar por nombre, apellido o cédula…")
        self.buscar_persona.textChanged.connect(self.refrescar_personas)
        btn_rep = QPushButton("Ver reporte")
        btn_rep.clicked.connect(self._reporte_desde_personas)
        btn_del = QPushButton("Eliminar")
        btn_del.setProperty("variant", "danger")
        btn_del.clicked.connect(self._eliminar_persona)
        lay.addWidget(row_widget(self.buscar_persona, None, btn_rep, btn_del))

        self.tbl_personas = Table(["ID", "Cédula", "Nombres", "Apellidos", "Email", "Cursos", "Aprobados"])
        self.tbl_personas.doubleClicked.connect(self._reporte_desde_personas)
        lay.addWidget(self.tbl_personas, 1)
        return w

    # ------------------------------------------------------------- cursos
    def _page_cursos(self) -> QWidget:
        w, lay, _ = self._page("Cursos", "Participantes organizados por curso")
        self.combo_curso = QComboBox()
        self.combo_curso.currentIndexChanged.connect(self.refrescar_participantes_curso)
        btn_estado = QPushButton("Cambiar estado")
        btn_estado.clicked.connect(self._cambiar_estado)
        btn_csv = QPushButton("Exportar CSV")
        btn_csv.setProperty("variant", "ghost")
        btn_csv.clicked.connect(self._exportar_curso)
        btn_delc = QPushButton("Eliminar curso")
        btn_delc.setProperty("variant", "danger")
        btn_delc.clicked.connect(self._eliminar_curso)
        lay.addWidget(row_widget(self.combo_curso, None, btn_estado, btn_csv, btn_delc))

        self.lbl_curso_info = QLabel("")
        self.lbl_curso_info.setObjectName("PageSub")
        lay.addWidget(self.lbl_curso_info)

        self.tbl_curso = Table(["Insc.", "Cédula", "Nombres", "Apellidos", "Estado", "Nota", "Asistencia", "Certif."])
        lay.addWidget(self.tbl_curso, 1)
        return w

    # ------------------------------------------------------------ importar
    def _page_importar(self) -> QWidget:
        w, lay, _ = self._page("Importar desde Excel",
                               "Carga participantes y cursos desde un archivo .xlsx, .xls o .csv")
        c = Card()
        cl = QVBoxLayout(c)
        cl.setContentsMargins(18, 16, 18, 18)
        cl.setSpacing(10)
        cl.addWidget(QLabel(
            "<b>Columnas reconocidas automáticamente</b><br>"
            "<span style='color:#6b7280'>Cédula · Nombres · Apellidos (o Nombre completo) · Email · Teléfono · "
            "<b>Curso</b> · Código · Instructor · Fecha inicio · Fecha fin · Horas · Estado · Nota · Asistencia · Observación"
            "</span>"))
        btn_sel = QPushButton("Seleccionar archivo…")
        btn_sel.clicked.connect(self._importar_excel)
        btn_plant = QPushButton("Descargar plantilla")
        btn_plant.setProperty("variant", "ghost")
        btn_plant.clicked.connect(self._plantilla)
        cl.addWidget(row_widget(btn_sel, btn_plant, None))
        lay.addWidget(c)

        self.log_import = QTextBrowser()
        self.log_import.setPlaceholderText("Aquí se mostrará el resultado de la importación.")
        lay.addWidget(self.log_import, 1)
        return w

    # -------------------------------------------------------- certificados
    def _page_certificados(self) -> QWidget:
        w, lay, _ = self._page("Certificados",
                               "El sistema lee el curso y el nombre del participante desde el archivo")
        btn = QPushButton("Cargar certificados…")
        btn.clicked.connect(self._cargar_certificados)
        self.buscar_cert = QLineEdit(placeholderText="Buscar por participante o curso…")
        self.buscar_cert.textChanged.connect(self.refrescar_certificados)
        btn_abrir = QPushButton("Abrir certificado")
        btn_abrir.setProperty("variant", "ghost")
        btn_abrir.clicked.connect(self._abrir_certificado)
        btn_carpeta = QPushButton("Abrir carpeta")
        btn_carpeta.setProperty("variant", "ghost")
        btn_carpeta.clicked.connect(lambda: abrir_archivo(CERT_DIR))
        lay.addWidget(row_widget(self.buscar_cert, None, btn, btn_abrir, btn_carpeta))

        self.tbl_cert = Table(["ID", "Participante", "Cédula", "Curso", "Archivo", "Cargado"])
        self.tbl_cert.doubleClicked.connect(self._abrir_certificado)
        lay.addWidget(self.tbl_cert, 1)
        return w

    # ------------------------------------------------------------ reportes
    def _page_reportes(self) -> QWidget:
        w, lay, _ = self._page("Reporte del participante",
                               "Cursos realizados, faltas, aprobaciones y certificados")
        self.combo_persona = QComboBox()
        self.combo_persona.setEditable(True)
        self.combo_persona.currentIndexChanged.connect(self.refrescar_reporte)
        btn_pdf = QPushButton("Exportar PDF")
        btn_pdf.clicked.connect(self._exportar_pdf)
        lay.addWidget(row_widget(self.combo_persona, None, btn_pdf))

        self.vista_reporte = QTextBrowser()
        lay.addWidget(self.vista_reporte, 1)
        return w

    # ============================================================ refrescos
    def refrescar_todo(self) -> None:
        self.refrescar_dashboard()
        self.refrescar_personas()
        self.refrescar_cursos()
        self.refrescar_certificados()
        self.refrescar_lista_personas()

    def refrescar_dashboard(self) -> None:
        r = self.db.resumen()
        for k, card in self.stats.items():
            card.set(r[k])
        filas = []
        for c in self.db.cursos():
            pct = f"{(c['aprobados'] / c['participantes'] * 100):.0f}%" if c["participantes"] else "—"
            filas.append([c["nombre"], c["codigo"] or "—", c["participantes"], c["aprobados"], c["faltas"], pct])
        self.tbl_dash.fill(filas)

    def refrescar_personas(self) -> None:
        filas = [[p["id"], p["cedula"] or "—", p["nombres"], p["apellidos"],
                  p["email"] or "—", p["cursos"], p["aprobados"]]
                 for p in self.db.personas(self.buscar_persona.text())]
        self.tbl_personas.fill(filas)

    def refrescar_cursos(self) -> None:
        actual = self.combo_curso.currentData()
        self.combo_curso.blockSignals(True)
        self.combo_curso.clear()
        for c in self.db.cursos():
            self.combo_curso.addItem(f"{c['nombre']}  ({c['participantes']} participantes)", c["id"])
        if actual is not None:
            i = self.combo_curso.findData(actual)
            if i >= 0:
                self.combo_curso.setCurrentIndex(i)
        self.combo_curso.blockSignals(False)
        self.refrescar_participantes_curso()

    def refrescar_participantes_curso(self) -> None:
        cid = self.combo_curso.currentData()
        if cid is None:
            self.tbl_curso.fill([])
            self.lbl_curso_info.setText("No hay cursos cargados todavía.")
            return
        c = self.db.q("SELECT * FROM cursos WHERE id=?", (cid,))[0]
        self.lbl_curso_info.setText(
            f"Código: {c['codigo'] or '—'} · Instructor: {c['instructor'] or '—'} · "
            f"Periodo: {c['fecha_inicio'] or '—'} a {c['fecha_fin'] or '—'} · Horas: {c['horas'] or '—'}")
        filas = [[p["inscripcion_id"], p["cedula"] or "—", p["nombres"], p["apellidos"],
                  p["estado"], p["nota"] if p["nota"] is not None else "—",
                  p["asistencia"] if p["asistencia"] is not None else "—", p["certificados"]]
                 for p in self.db.participantes_de_curso(cid)]
        self.tbl_curso.fill(filas, columna_estado=4)

    def refrescar_certificados(self) -> None:
        filas = [[c["id"], f"{c['nombres']} {c['apellidos']}", c["cedula"] or "—",
                  c["curso"], c["nombre_archivo"], c["cargado_en"][:16].replace("T", " ")]
                 for c in self.db.certificados(self.buscar_cert.text())]
        self.tbl_cert.fill(filas)

    def refrescar_lista_personas(self) -> None:
        actual = self.combo_persona.currentData()
        self.combo_persona.blockSignals(True)
        self.combo_persona.clear()
        for p in self.db.personas():
            self.combo_persona.addItem(f"{p['apellidos']}, {p['nombres']}", p["id"])
        if actual is not None:
            i = self.combo_persona.findData(actual)
            if i >= 0:
                self.combo_persona.setCurrentIndex(i)
        self.combo_persona.blockSignals(False)
        self.refrescar_reporte()

    def refrescar_reporte(self) -> None:
        pid = self.combo_persona.currentData()
        if pid is None:
            self.vista_reporte.setHtml("<p style='color:#6b7280'>Sin participantes registrados.</p>")
            return
        self.vista_reporte.setHtml(reportes.reporte_persona_html(self.db, pid))

    # ============================================================= acciones
    def _fila_sel(self, tabla: Table) -> int | None:
        r = tabla.currentRow()
        return None if r < 0 else r

    def _reporte_desde_personas(self) -> None:
        r = self._fila_sel(self.tbl_personas)
        if r is None:
            QMessageBox.information(self, "Reporte", "Selecciona un participante.")
            return
        pid = int(self.tbl_personas.item(r, 0).text())
        i = self.combo_persona.findData(pid)
        if i >= 0:
            self.combo_persona.setCurrentIndex(i)
        self.menu_group.button(5).setChecked(True)
        self.stack.setCurrentIndex(5)
        self.refrescar_reporte()

    def _eliminar_persona(self) -> None:
        r = self._fila_sel(self.tbl_personas)
        if r is None:
            return
        pid = int(self.tbl_personas.item(r, 0).text())
        nombre = f"{self.tbl_personas.item(r, 2).text()} {self.tbl_personas.item(r, 3).text()}"
        if QMessageBox.question(self, "Eliminar", f"¿Eliminar a {nombre} y todo su historial?") == QMessageBox.Yes:
            self.db.eliminar_persona(pid)
            self.refrescar_todo()

    def _eliminar_curso(self) -> None:
        cid = self.combo_curso.currentData()
        if cid is None:
            return
        if QMessageBox.question(self, "Eliminar curso",
                                "¿Eliminar el curso y sus inscripciones?") == QMessageBox.Yes:
            self.db.eliminar_curso(cid)
            self.refrescar_todo()

    def _cambiar_estado(self) -> None:
        r = self._fila_sel(self.tbl_curso)
        if r is None:
            QMessageBox.information(self, "Estado", "Selecciona un participante.")
            return
        insc = int(self.tbl_curso.item(r, 0).text())
        actual = self.tbl_curso.item(r, 4).text()
        estado, ok = QInputDialog.getItem(self, "Cambiar estado", "Nuevo estado:",
                                          ESTADOS, ESTADOS.index(actual) if actual in ESTADOS else 0, False)
        if ok:
            self.db.set_estado(insc, estado)
            self.refrescar_todo()

    def _exportar_curso(self) -> None:
        cid = self.combo_curso.currentData()
        if cid is None:
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", "participantes.csv", "CSV (*.csv)")
        if ruta:
            reportes.exportar_csv_curso(self.db, cid, ruta)
            QMessageBox.information(self, "Exportado", f"Archivo guardado en:\n{ruta}")

    def _plantilla(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar plantilla", "plantilla_participantes.xlsx",
                                              "Excel (*.xlsx)")
        if not ruta:
            return
        import pandas as pd
        pd.DataFrame([{
            "Cedula": "V-12345678", "Nombres": "María José", "Apellidos": "Pérez Rojas",
            "Email": "maria@correo.com", "Telefono": "0412-0000000",
            "Curso": "Seguridad Industrial", "Codigo": "SI-01", "Instructor": "Ing. López",
            "Fecha Inicio": "2026-01-15", "Fecha Fin": "2026-01-20", "Horas": 16,
            "Estado": "Aprobado", "Nota": 18.5, "Asistencia": 100, "Observacion": "",
        }]).to_excel(ruta, index=False)
        QMessageBox.information(self, "Plantilla", f"Plantilla creada en:\n{ruta}")

    def _importar_excel(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "",
                                              "Excel/CSV (*.xlsx *.xls *.csv)")
        if not ruta:
            return
        try:
            hojas = importer.hojas_de(ruta)
            hoja = hojas[0]
            if len(hojas) > 1:
                hoja, ok = QInputDialog.getItem(self, "Hoja", "Selecciona la hoja:", hojas, 0, False)
                if not ok:
                    return
            df = importer.leer_archivo(ruta, hoja)
            mapa = importer.mapear_columnas(list(df.columns))
            curso_defecto = None
            if "curso" not in mapa:
                curso_defecto, ok = QInputDialog.getText(
                    self, "Curso", "El archivo no tiene columna 'Curso'.\nNombre del curso para todas las filas:")
                if not ok or not curso_defecto.strip():
                    return
            res = importer.importar(self.db, df, curso_defecto, mapa)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", f"No se pudo importar:\n{exc}")
            return

        detalle = "<br>".join(res.errores[:30]) or "—"
        self.log_import.setHtml(
            f"<b>Archivo:</b> {os.path.basename(ruta)}<br>"
            f"<b>Columnas detectadas:</b> {', '.join(f'{k} → {v}' for k, v in mapa.items()) or '—'}<br><br>"
            f"<b>Filas procesadas:</b> {res.filas}<br>"
            f"<b>Personas nuevas:</b> {res.personas_nuevas}<br>"
            f"<b>Cursos nuevos:</b> {res.cursos_nuevos}<br>"
            f"<b>Inscripciones:</b> {res.inscripciones}<br>"
            f"<b>Errores ({len(res.errores)}):</b><br>{detalle}")
        self.refrescar_todo()
        QMessageBox.information(self, "Importación completada", res.resumen())

    def _cargar_certificados(self) -> None:
        rutas, _ = QFileDialog.getOpenFileNames(self, "Seleccionar certificados", "",
                                                "Certificados (*.pdf *.png *.jpg *.jpeg)")
        if not rutas:
            return
        ok_list, fallidos = [], []
        for ruta in rutas:
            d = cert_mod.analizar(self.db, ruta)
            (ok_list if d.ok else fallidos).append(d)

        if ok_list:
            detalle = "\n".join(f"• {os.path.basename(d.archivo)} → {d.persona} / {d.curso} [{d.estado}]"
                                for d in ok_list[:15])
            resp = QMessageBox.question(
                self, "Confirmar",
                f"Se identificaron {len(ok_list)} certificado(s):\n\n{detalle}\n\n"
                "¿Guardar y marcar como Aprobado a quien no lo esté?")
            if resp == QMessageBox.Yes:
                for d in ok_list:
                    cert_mod.guardar(self.db, d, aprobar=True)
        if fallidos:
            QMessageBox.warning(
                self, "No identificados",
                "\n".join(f"• {os.path.basename(d.archivo)}: {d.mensaje}" for d in fallidos[:15]))
        self.refrescar_todo()

    def _abrir_certificado(self) -> None:
        r = self._fila_sel(self.tbl_cert)
        if r is None:
            return
        cid = int(self.tbl_cert.item(r, 0).text())
        row = self.db.q("SELECT archivo FROM certificados WHERE id=?", (cid,))
        if row and os.path.exists(row[0]["archivo"]):
            abrir_archivo(row[0]["archivo"])
        else:
            QMessageBox.warning(self, "Archivo", "El archivo ya no existe en disco.")

    def _exportar_pdf(self) -> None:
        pid = self.combo_persona.currentData()
        if pid is None:
            return
        p = self.db.q("SELECT nombres, apellidos FROM personas WHERE id=?", (pid,))[0]
        base = f"reporte_{p['apellidos']}_{p['nombres']}".replace(" ", "_")
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar reporte", f"{base}.pdf", "PDF (*.pdf)")
        if ruta:
            reportes.exportar_pdf(reportes.reporte_persona_html(self.db, pid), ruta)
            QMessageBox.information(self, "Reporte", f"Reporte guardado en:\n{ruta}")
