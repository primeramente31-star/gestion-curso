"""Widgets reutilizables."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QHeaderView, QLabel,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from .theme import ESTADO_COLOR


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")


class StatCard(Card):
    def __init__(self, label: str, valor="0", parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(2)
        self.valor = QLabel(str(valor))
        self.valor.setObjectName("StatValue")
        titulo = QLabel(label)
        titulo.setObjectName("StatLabel")
        lay.addWidget(self.valor)
        lay.addWidget(titulo)
        self.setMinimumHeight(84)

    def set(self, valor) -> None:
        self.valor.setText(str(valor))


class PageHeader(QWidget):
    def __init__(self, titulo: str, subtitulo: str = "", parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        t = QLabel(titulo)
        t.setObjectName("PageTitle")
        self.sub = QLabel(subtitulo)
        self.sub.setObjectName("PageSub")
        lay.addWidget(t)
        lay.addWidget(self.sub)


class Table(QTableWidget):
    def __init__(self, headers: list[str], parent=None):
        super().__init__(0, len(headers), parent)
        self.setHorizontalHeaderLabels(headers)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setDefaultSectionSize(38)

    def fill(self, filas: list[list], columna_estado: int | None = None) -> None:
        self.setRowCount(0)
        for fila in filas:
            r = self.rowCount()
            self.insertRow(r)
            for c, valor in enumerate(fila):
                item = QTableWidgetItem("" if valor is None else str(valor))
                if columna_estado is not None and c == columna_estado:
                    color = ESTADO_COLOR.get(str(valor))
                    if color:
                        item.setForeground(QColor(color))
                        f = item.font()
                        f.setBold(True)
                        item.setFont(f)
                    item.setTextAlignment(Qt.AlignCenter)
                self.setItem(r, c, item)


def row_widget(*widgets, spacing=8, margins=(0, 0, 0, 0)) -> QWidget:
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(*margins)
    lay.setSpacing(spacing)
    for x in widgets:
        if x is None:
            lay.addStretch()
        else:
            lay.addWidget(x)
    return w
