"""Diálogo para crear o editar un sector. Cada campo lleva su texto de ayuda.

Los campos de lista se editan como texto, un término por línea. Al guardar se
valida con Sector.from_dict y se persiste como JSON.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from compscrapper import config
from compscrapper.models import Sector
from . import ayuda
from .selector_geografico import SelectorGeografico


def _lineas(texto: str) -> list[str]:
    return [ln.strip() for ln in texto.splitlines() if ln.strip()]


def _texto(items: list[str]) -> str:
    return "\n".join(items)


class EditorSector(QDialog):
    def __init__(self, sector: Sector | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar sector" if sector else "Nuevo sector")
        self.resize(860, 720)
        self._original_nombre = sector.nombre if sector else None

        cont = QWidget()
        form = QFormLayout(cont)

        self.txt_nombre = QLineEdit()
        self.txt_descripcion = QPlainTextEdit()
        self.txt_sector = QPlainTextEdit()
        self.txt_queja = QPlainTextEdit()
        self.txt_contexto = QPlainTextEdit()
        self.txt_consultas = QPlainTextEdit()
        self.txt_descubrimiento = QPlainTextEdit()
        self.txt_exclusiones = QPlainTextEdit()
        self.txt_dominios = QPlainTextEdit()
        self.selector_geo = SelectorGeografico()

        self._fila(form, "Nombre", self.txt_nombre, ayuda.NOMBRE)
        self._fila(form, "Descripción", self.txt_descripcion, ayuda.DESCRIPCION)
        self._fila(form, "Términos del sector", self.txt_sector, ayuda.TERMINOS_SECTOR)
        self._fila(form, "Términos de queja/competencia", self.txt_queja, ayuda.TERMINOS_QUEJA)
        self._fila(form, "Términos de contexto", self.txt_contexto, ayuda.TERMINOS_CONTEXTO)
        self._fila(form, "Consultas", self.txt_consultas, ayuda.CONSULTAS)
        self._fila(form, "Consultas de descubrimiento", self.txt_descubrimiento,
                   ayuda.CONSULTAS_DESCUBRIMIENTO)
        self._fila(form, "Exclusiones", self.txt_exclusiones, ayuda.EXCLUSIONES)
        self._fila(form, "Fuentes del sector", self.txt_dominios, ayuda.DOMINIOS_FUENTE)
        form.addRow("Ámbito geográfico", self.selector_geo)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(cont)

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Save).setObjectName("primary")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll)
        layout.addWidget(botones)

        if sector:
            self._cargar(sector)

    def _fila(self, form, etiqueta, widget, texto_ayuda) -> None:
        if isinstance(widget, QPlainTextEdit):
            widget.setMaximumHeight(90)
        form.addRow(etiqueta, widget)
        # La ayuda va en su propia fila, ocupando ambas columnas, para que el
        # texto disponga de todo el ancho del diálogo y no se corte.
        ayuda_lbl = QLabel(texto_ayuda, wordWrap=True)
        ayuda_lbl.setStyleSheet("color: #555; font-size: 11px; padding-bottom: 6px;")
        form.addRow(ayuda_lbl)

    def _cargar(self, s: Sector) -> None:
        self.txt_nombre.setText(s.nombre)
        self.txt_descripcion.setPlainText(s.descripcion)
        self.txt_sector.setPlainText(_texto(s.terminos_sector))
        self.txt_queja.setPlainText(_texto(s.terminos_queja))
        self.txt_contexto.setPlainText(_texto(s.terminos_contexto))
        self.txt_consultas.setPlainText(_texto(s.consultas))
        self.txt_descubrimiento.setPlainText(_texto(s.consultas_descubrimiento))
        self.txt_exclusiones.setPlainText(_texto(s.exclusiones))
        self.txt_dominios.setPlainText(_texto(s.dominios_fuente))
        self.selector_geo.set_ambito(s.ambito_geografico)

    def sector_actual(self) -> Sector:
        return Sector.from_dict({
            "nombre": self.txt_nombre.text(),
            "descripcion": self.txt_descripcion.toPlainText().strip(),
            "terminos_sector": _lineas(self.txt_sector.toPlainText()),
            "terminos_queja": _lineas(self.txt_queja.toPlainText()),
            "terminos_contexto": _lineas(self.txt_contexto.toPlainText()),
            "consultas": _lineas(self.txt_consultas.toPlainText()),
            "consultas_descubrimiento": _lineas(self.txt_descubrimiento.toPlainText()),
            "exclusiones": _lineas(self.txt_exclusiones.toPlainText()),
            "dominios_fuente": _lineas(self.txt_dominios.toPlainText()),
            "ambito_geografico": self.selector_geo.ambito(),
        })

    def _guardar(self) -> None:
        try:
            sector = self.sector_actual()
        except ValueError as e:
            QMessageBox.warning(self, "Datos incompletos", str(e))
            return
        if not sector.consultas:
            QMessageBox.warning(self, "Falta información",
                                "Agregá al menos una consulta de búsqueda.")
            return
        # Si se renombró, borrar el archivo anterior.
        if self._original_nombre and self._original_nombre != sector.nombre:
            config.delete_sector(self._original_nombre)
        config.save_sector(sector)
        self.sector_guardado = sector
        self.accept()
