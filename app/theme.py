"""Tema visual de la aplicación.

Todo el estilo vive aquí para poder adaptarlo a un diseño de referencia
sin tocar la lógica de la aplicación.
"""

COLORS = {
    "bg": "#f5f6fa",
    "sidebar": "#111827",
    "sidebar_hover": "#1f2937",
    "accent": "#2563eb",
    "card": "#ffffff",
    "text": "#111827",
    "muted": "#6b7280",
    "border": "#e5e7eb",
    "green": "#16a34a",
    "red": "#dc2626",
    "amber": "#d97706",
}

STYLESHEET = f"""
QWidget {{
    font-family: 'Segoe UI', 'Noto Sans', Arial, sans-serif;
    font-size: 13px;
    color: {COLORS['text']};
}}
QMainWindow, #Content {{ background: {COLORS['bg']}; }}

/* ------------------------------------------------------------- Sidebar */
#Sidebar {{ background: {COLORS['sidebar']}; }}
#Logo {{
    color: #ffffff; font-size: 16px; font-weight: 700;
    padding: 22px 18px 6px 18px;
}}
#LogoSub {{ color: #9ca3af; font-size: 11px; padding: 0 18px 18px 18px; }}
#Sidebar QPushButton {{
    background: transparent; color: #d1d5db; border: none;
    text-align: left; padding: 11px 18px; border-radius: 8px;
    margin: 2px 10px; font-size: 13px;
}}
#Sidebar QPushButton:hover {{ background: {COLORS['sidebar_hover']}; color: #ffffff; }}
#Sidebar QPushButton:checked {{ background: {COLORS['accent']}; color: #ffffff; font-weight: 600; }}

/* -------------------------------------------------------------- Header */
#PageTitle {{ font-size: 22px; font-weight: 700; }}
#PageSub {{ color: {COLORS['muted']}; font-size: 12px; }}

/* --------------------------------------------------------------- Cards */
#Card {{
    background: {COLORS['card']}; border: 1px solid {COLORS['border']};
    border-radius: 12px;
}}
#StatValue {{ font-size: 26px; font-weight: 700; }}
#StatLabel {{ color: {COLORS['muted']}; font-size: 11px; text-transform: uppercase; }}

/* -------------------------------------------------------------- Tablas */
QTableWidget {{
    background: {COLORS['card']}; border: 1px solid {COLORS['border']};
    border-radius: 10px; gridline-color: transparent;
    selection-background-color: #dbeafe; selection-color: {COLORS['text']};
}}
QTableWidget::item {{ padding: 6px; border-bottom: 1px solid #f1f2f6; }}
QHeaderView::section {{
    background: #f9fafb; color: {COLORS['muted']}; border: none;
    border-bottom: 1px solid {COLORS['border']}; padding: 9px; font-weight: 600;
}}

/* ------------------------------------------------------------ Controles */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    background: #ffffff; border: 1px solid {COLORS['border']};
    border-radius: 8px; padding: 7px 10px; min-height: 18px;
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {COLORS['accent']}; }}
QPushButton {{
    background: {COLORS['accent']}; color: #ffffff; border: none;
    border-radius: 8px; padding: 9px 16px; font-weight: 600;
}}
QPushButton:hover {{ background: #1d4ed8; }}
QPushButton:disabled {{ background: #cbd5e1; color: #eef2f7; }}
QPushButton[variant="ghost"] {{
    background: #ffffff; color: {COLORS['text']}; border: 1px solid {COLORS['border']};
}}
QPushButton[variant="ghost"]:hover {{ background: #f3f4f6; }}
QPushButton[variant="danger"] {{ background: {COLORS['red']}; }}
QTextBrowser {{
    background: #ffffff; border: 1px solid {COLORS['border']}; border-radius: 10px;
}}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px; }}
QScrollBar::handle:vertical {{ background: #cbd5e1; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
"""

ESTADO_COLOR = {
    "Aprobado": COLORS["green"],
    "Reprobado": COLORS["red"],
    "Faltó": COLORS["amber"],
    "Inscrito": COLORS["accent"],
}
