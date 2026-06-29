"""Diálogo "Crear sector con ayuda de IA".

La app no llama a ninguna IA: arma un prompt para que el usuario lo pegue en la
IA que prefiera, y recibe de vuelta el JSON del sector para importarlo. Flujo:
  1. describir el mercado;
  2. copiar el prompt y pegarlo en ChatGPT/Claude/etc.;
  3. pegar acá el JSON que devolvió la IA y crear el sector.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from compscrapper import config
from compscrapper.prompt import build_prompt, sector_desde_texto_ia


def _ayuda(texto: str) -> QLabel:
    lbl = QLabel(texto, wordWrap=True)
    lbl.setStyleSheet("color: #555; font-size: 11px;")
    return lbl


class AsistenteIA(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear sector con ayuda de IA")
        self.resize(720, 640)
        self.sector_creado = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "<b>La app no usa IA.</b> Te arma un prompt para que lo pegues en la IA "
            "que prefieras (ChatGPT, Claude, Gemini) y traigas el resultado.", wordWrap=True))

        # Paso 1: descripción
        layout.addWidget(QLabel("<b>1.</b> Describí tu mercado y la sospecha de competencia:"))
        self.txt_desc = QPlainTextEdit()
        self.txt_desc.setPlaceholderText(
            "Ej.: Combustibles en Paraguay. Sospechas de coordinación de precios "
            "entre estaciones de servicio y distribuidoras.")
        self.txt_desc.setMaximumHeight(90)
        layout.addWidget(self.txt_desc)

        # Paso 2: copiar el prompt
        layout.addWidget(QLabel("<b>2.</b> Copiá el prompt y pegalo en tu IA:"))
        self.btn_copiar = QPushButton("Copiar prompt al portapapeles")
        self.btn_copiar.clicked.connect(self._copiar_prompt)
        layout.addWidget(self.btn_copiar)
        layout.addWidget(_ayuda(
            "Pegá el prompt en la IA, esperá su respuesta y copiá el JSON que devuelve."))

        # Paso 3: pegar el JSON
        layout.addWidget(QLabel("<b>3.</b> Pegá acá el JSON que devolvió la IA:"))
        self.txt_json = QPlainTextEdit()
        self.txt_json.setPlaceholderText('{ "nombre": "...", "terminos_sector": [...], ... }')
        layout.addWidget(self.txt_json, 1)
        layout.addWidget(_ayuda(
            "No importa si la IA agregó texto alrededor; se toma el primer objeto JSON."))

        botones = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.btn_crear = botones.addButton("Crear sector", QDialogButtonBox.AcceptRole)
        self.btn_crear.setObjectName("primary")
        self.btn_crear.clicked.connect(self._crear)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _copiar_prompt(self) -> None:
        prompt = build_prompt(self.txt_desc.toPlainText())
        QApplication.clipboard().setText(prompt)
        self.btn_copiar.setText("✓ Prompt copiado — pegalo en tu IA")

    def _crear(self) -> None:
        try:
            sector = sector_desde_texto_ia(self.txt_json.toPlainText())
        except ValueError as e:
            QMessageBox.warning(self, "No se pudo crear el sector", str(e))
            return
        if not sector.consultas:
            QMessageBox.warning(self, "Falta información",
                                "El sector necesita al menos una consulta de búsqueda.")
            return
        if config.sector_path(sector.nombre).exists():
            if QMessageBox.question(
                self, "El sector ya existe",
                f"Ya hay un sector llamado '{sector.nombre}'. ¿Reemplazarlo?"
            ) != QMessageBox.Yes:
                return
        config.save_sector(sector)
        self.sector_creado = sector
        self.accept()
