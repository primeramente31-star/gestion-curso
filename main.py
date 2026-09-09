"""Punto de entrada del Sistema de Gestión de Cursos (escritorio)."""
import sys

from PySide6.QtWidgets import QApplication

from app.db import Database
from app.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Sistema de Gestión de Cursos")
    win = MainWindow(Database())
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
