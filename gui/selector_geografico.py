"""Selector geográfico jerárquico: país → departamentos → ciudades.

Un árbol con casillas tri-estado: marcar un departamento marca todas sus
ciudades; marcar algunas ciudades deja el departamento en estado parcial. Una
casilla "Nacional" arriba cubre todo el país (sin restricción) y deshabilita el
árbol.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from compscrapper import geo
from . import ayuda


class SelectorGeografico(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel(ayuda.AMBITO_GEOGRAFICO, wordWrap=True))

        self.chk_nacional = QCheckBox("Nacional (todo el país)")
        self.chk_nacional.setChecked(True)
        self.chk_nacional.toggled.connect(self._on_nacional)
        layout.addWidget(self.chk_nacional)

        self.arbol = QTreeWidget()
        self.arbol.setHeaderLabel("Departamentos y ciudades")
        self.arbol.setEnabled(False)
        self._poblar()
        layout.addWidget(self.arbol)

    def _poblar(self) -> None:
        for dep in geo.departamentos():
            item_dep = QTreeWidgetItem(self.arbol, [dep])
            item_dep.setFlags(
                item_dep.flags()
                | Qt.ItemIsUserCheckable
                | Qt.ItemIsAutoTristate
            )
            item_dep.setCheckState(0, Qt.Unchecked)
            for ciudad in geo.ciudades(dep):
                item_ciu = QTreeWidgetItem(item_dep, [ciudad])
                item_ciu.setFlags(item_ciu.flags() | Qt.ItemIsUserCheckable)
                item_ciu.setCheckState(0, Qt.Unchecked)

    def _on_nacional(self, nacional: bool) -> None:
        self.arbol.setEnabled(not nacional)

    # -- API --
    def ambito(self) -> list[str]:
        """Lista plana de términos de lugar (vacío = nacional)."""
        if self.chk_nacional.isChecked():
            return []
        departamentos, ciudades = [], []
        for i in range(self.arbol.topLevelItemCount()):
            dep_item = self.arbol.topLevelItem(i)
            estado = dep_item.checkState(0)
            if estado == Qt.Checked:
                departamentos.append(dep_item.text(0))
            elif estado == Qt.PartiallyChecked:
                for j in range(dep_item.childCount()):
                    ciu = dep_item.child(j)
                    if ciu.checkState(0) == Qt.Checked:
                        ciudades.append(ciu.text(0))
        return geo.resolver({"departamentos": departamentos, "ciudades": ciudades})

    def set_ambito(self, terminos: list[str]) -> None:
        """Reconstruye la selección a partir de una lista de lugares (mejor esfuerzo)."""
        deseados = set(terminos)
        self.chk_nacional.setChecked(not deseados)
        self.arbol.setEnabled(bool(deseados))
        for i in range(self.arbol.topLevelItemCount()):
            dep_item = self.arbol.topLevelItem(i)
            dep_marcado = dep_item.text(0) in deseados
            for j in range(dep_item.childCount()):
                ciu = dep_item.child(j)
                marcar = dep_marcado or ciu.text(0) in deseados
                ciu.setCheckState(0, Qt.Checked if marcar else Qt.Unchecked)
