"""Estilo visual global de la app (hoja de estilos Qt).

Paleta institucional alineada al logo de CONACOM (azul pizarra). Se aplica una
sola vez en `app.py` con `aplicar(app)`; no toca la lógica. Es portable Mac+Windows.
"""

from __future__ import annotations

from PySide6.QtGui import QIcon, QPixmap

from compscrapper import config

# Paleta -------------------------------------------------------------------
ACENTO = "#3a5a78"        # azul pizarra del logo CONACOM
ACENTO_HOVER = "#2f4a63"
ACENTO_PRESS = "#284054"
PAGINA = "#f4f6f8"
SUPERFICIE = "#ffffff"
BORDE = "#dfe3e8"
TEXTO = "#1f2a37"
SUAVE = "#5b6675"

# Colores del chip de relevancia (fondo, texto) por nivel.
RELEVANCIA_COLORES = {
    3: ("#dce8f2", "#24435e"),  # alto  — azul pizarra
    2: ("#fbeecf", "#7a5310"),  # medio — ámbar
    1: ("#eceef1", "#5b6675"),  # bajo  — gris
}

QSS = f"""
QMainWindow, QDialog, QStackedWidget {{ background: {PAGINA}; }}
QWidget {{ color: {TEXTO}; font-size: 14px; }}
QLabel {{ color: {TEXTO}; background: transparent; }}

QFrame#card {{ background: {SUPERFICIE}; border: 1px solid {BORDE}; border-radius: 12px; }}
QFrame#header {{
    background: {SUPERFICIE}; border: none; border-bottom: 1px solid {BORDE};
    border-top-left-radius: 12px; border-top-right-radius: 12px;
}}
QFrame#sep {{ color: {BORDE}; max-width: 1px; }}
QLabel#banner {{
    background: #e9eff5; color: {ACENTO}; border: 1px solid #c7d6e3;
    border-radius: 8px; padding: 8px 12px;
}}
QFrame#update {{ background: #fbeecf; border: 1px solid #e7c97a; border-radius: 8px; }}
QFrame#update QLabel {{ color: #7a5310; }}

QPushButton {{
    background: {SUPERFICIE}; border: 1px solid {BORDE}; border-radius: 6px;
    padding: 6px 12px; color: {TEXTO};
}}
QPushButton:hover {{ background: #eef1f4; }}
QPushButton:pressed {{ background: #e4e8ec; }}
QPushButton:disabled {{ color: #9aa3ad; }}
QPushButton#primary {{
    background: {ACENTO}; border: 1px solid {ACENTO}; color: white; font-weight: 500;
    padding: 8px 16px;
}}
QPushButton#primary:hover {{ background: {ACENTO_HOVER}; border-color: {ACENTO_HOVER}; }}
QPushButton#primary:pressed {{ background: {ACENTO_PRESS}; border-color: {ACENTO_PRESS}; }}
QPushButton#acento {{ background: #e9eff5; border: 1px solid #c7d6e3; color: {ACENTO}; }}
QPushButton#acento:hover {{ background: #dde7f0; }}

QLineEdit, QPlainTextEdit, QComboBox, QDateEdit {{
    background: {SUPERFICIE}; border: 1px solid {BORDE}; border-radius: 6px; padding: 5px 8px;
    selection-background-color: {ACENTO}; selection-color: white;
}}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QDateEdit:focus {{ border: 1px solid {ACENTO}; }}
QComboBox::drop-down, QDateEdit::drop-down {{ border: none; width: 22px; }}

QGroupBox {{
    background: {SUPERFICIE}; border: 1px solid {BORDE}; border-radius: 8px;
    margin-top: 12px; padding: 12px;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {SUAVE}; }}

QTabWidget::pane {{ border: 1px solid {BORDE}; border-radius: 8px; background: {SUPERFICIE}; top: -1px; }}
QTabBar::tab {{ background: transparent; padding: 8px 16px; color: {SUAVE}; border: none; border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {ACENTO}; border-bottom: 2px solid {ACENTO}; }}

QTableWidget {{ background: {SUPERFICIE}; border: none; gridline-color: #eef1f4; }}
QHeaderView::section {{
    background: #f0f3f6; color: {SUAVE}; border: none; border-bottom: 1px solid {BORDE};
    padding: 6px 8px; font-weight: 500;
}}
QTableWidget::item {{ padding: 4px 6px; }}
QTableWidget::item:selected {{ background: #e9eff5; color: {TEXTO}; }}

QCheckBox {{ spacing: 8px; background: transparent; }}
QScrollArea {{ border: none; background: transparent; }}

QProgressBar {{
    border: 1px solid {BORDE}; border-radius: 6px; background: #eef1f4;
    text-align: center; height: 22px; color: {TEXTO};
}}
QProgressBar::chunk {{ background: {ACENTO}; border-radius: 5px; }}
"""


def logo_pixmap() -> QPixmap:
    """Logo transparente para el encabezado (emblema + CONACOM)."""
    for nombre in ("logo.png", "logo.jpeg"):
        ruta = config.archivo_datos(nombre)
        if ruta.exists():
            return QPixmap(str(ruta))
    return QPixmap()


def icono_pixmap() -> QPixmap:
    """Ícono de la app: cuadrado con fondo blanco y puntas redondeadas."""
    ruta = config.archivo_datos("icono.png")
    return QPixmap(str(ruta)) if ruta.exists() else logo_pixmap()


def aplicar(app) -> None:
    """Aplica la hoja de estilos y el ícono de la app."""
    app.setStyleSheet(QSS)
    pm = icono_pixmap()
    if not pm.isNull():
        app.setWindowIcon(QIcon(pm))
