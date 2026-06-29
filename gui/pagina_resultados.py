"""Pantalla de resultados: filtro manual de noticias, actores y exportación."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from compscrapper import __version__, config
from compscrapper.export import export_excel
from compscrapper.suggest import MENSAJE_SUGERENCIA, es_relacionado_contrataciones
from .estilo import RELEVANCIA_COLORES


def _link_label(url: str) -> QLabel:
    from urllib.parse import urlsplit
    texto = urlsplit(url).netloc.replace("www.", "") if url else ""
    lbl = QLabel(f'<a href="{url}">{texto}</a>')
    lbl.setOpenExternalLinks(True)  # abre en el navegador del sistema
    lbl.setToolTip(url)
    return lbl


class PaginaResultados(QWidget):
    volver = Signal()

    COLS = ["Mantener", "Relev.", "Título", "Fuente", "Fecha", "Enlace", "Resaltado"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._noticias = []
        self._actores = []
        self._sector = None
        self._desde = None
        self._hasta = None

        layout = QVBoxLayout(self)

        self.banner = QLabel(MENSAJE_SUGERENCIA, wordWrap=True)
        self.banner.setObjectName("banner")
        self.banner.setVisible(False)
        layout.addWidget(self.banner)

        self.lbl_resumen = QLabel("")
        layout.addWidget(self.lbl_resumen)

        self.tabs = QTabWidget()
        self.tabla = QTableWidget(0, len(self.COLS))
        self.tabla.setHorizontalHeaderLabels(self.COLS)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.tabla, "Noticias")

        self.tabla_actores = QTableWidget(0, 4)
        self.tabla_actores.setHorizontalHeaderLabels(
            ["Mantener", "Actor candidato", "Menciones", "Ejemplo"])
        self.tabla_actores.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.tabla_actores, "Actores candidatos")
        layout.addWidget(self.tabs)

        botones = QHBoxLayout()
        self.btn_volver = QPushButton("◄ Volver")
        self.btn_volver.clicked.connect(self.volver.emit)
        botones.addWidget(self.btn_volver)
        botones.addStretch(1)
        self.btn_promover = QPushButton("➕ Agregar actores marcados al sector")
        self.btn_promover.setToolTip(
            "Suma los actores marcados (Mantener) a los términos del sector. "
            "La próxima búsqueda los incluirá.")
        self.btn_promover.clicked.connect(self._promover_actores)
        botones.addWidget(self.btn_promover)
        self.btn_exportar = QPushButton("Exportar Excel")
        self.btn_exportar.setObjectName("primary")
        self.btn_exportar.clicked.connect(self._exportar)
        botones.addWidget(self.btn_exportar)
        layout.addLayout(botones)

    @staticmethod
    def _chip_relevancia(nivel: int) -> QLabel:
        fondo, texto = RELEVANCIA_COLORES.get(nivel, RELEVANCIA_COLORES[1])
        lbl = QLabel(str(nivel))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"background: {fondo}; color: {texto}; border-radius: 10px; "
            "font-weight: 600; margin: 6px 14px;")
        return lbl

    def mostrar(self, noticias, actores, sector, desde, hasta) -> None:
        self._noticias = noticias
        self._actores = actores
        self._sector = sector
        self._desde = desde
        self._hasta = hasta

        self.banner.setVisible(es_relacionado_contrataciones(sector))
        n3 = sum(1 for n in noticias if n.relevancia == 3)
        self.lbl_resumen.setText(
            f"{len(noticias)} noticias (relevancia 3: {n3}) · "
            f"{len(actores)} actores candidatos. "
            "Desmarcá las que no apliquen antes de exportar.")

        self.tabla.setRowCount(len(noticias))
        for fila, n in enumerate(noticias):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Checked if n.mantener else Qt.Unchecked)
            self.tabla.setItem(fila, 0, chk)

            self.tabla.setCellWidget(fila, 1, self._chip_relevancia(n.relevancia))

            for col, valor in (
                (2, n.titulo),
                (3, n.fuente),
                (4, n.fecha_publicacion.strftime("%Y-%m-%d") if n.fecha_publicacion else ""),
            ):
                item = QTableWidgetItem(valor)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # no editable
                self.tabla.setItem(fila, col, item)

            self.tabla.setCellWidget(fila, 5, _link_label(n.url))
            self.tabla.setCellWidget(fila, 6, _link_label(n.url_resaltado))
        self.tabla.resizeColumnsToContents()
        self.tabla.setColumnWidth(0, 72)   # Mantener
        self.tabla.setColumnWidth(1, 64)   # chip de relevancia

        self.tabla_actores.setRowCount(len(actores))
        for fila, a in enumerate(actores):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Checked if a.mantener else Qt.Unchecked)
            self.tabla_actores.setItem(fila, 0, chk)
            for col, valor in (
                (1, a.candidato),
                (2, str(a.menciones)),
                (3, a.titular_ejemplo),
            ):
                item = QTableWidgetItem(valor)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # no editable
                self.tabla_actores.setItem(fila, col, item)

    def _sincronizar(self) -> None:
        """Vuelca el estado de las tablas (mantener, relevancia) a los objetos."""
        for fila, n in enumerate(self._noticias):
            n.mantener = self.tabla.item(fila, 0).checkState() == Qt.Checked
            try:
                n.relevancia = int(self.tabla.item(fila, 1).text())
            except (ValueError, AttributeError):
                pass
        for fila, a in enumerate(self._actores):
            a.mantener = self.tabla_actores.item(fila, 0).checkState() == Qt.Checked

    def _promover_actores(self) -> None:
        """Agrega los actores marcados a terminos_sector del sector y lo guarda."""
        if not self._sector:
            return
        self._sincronizar()
        marcados = [a.candidato.strip() for a in self._actores if a.mantener and a.candidato.strip()]
        if not marcados:
            QMessageBox.information(self, "Sin actores marcados",
                                    "Marcá (Mantener) los actores que quieras agregar al sector.")
            return
        existentes = {t.lower() for t in self._sector.terminos_sector}
        nuevos = [c for c in dict.fromkeys(marcados) if c.lower() not in existentes]
        if not nuevos:
            QMessageBox.information(self, "Ya estaban",
                                    "Los actores marcados ya forman parte del sector.")
            return
        self._sector.terminos_sector += nuevos
        config.save_sector(self._sector)
        QMessageBox.information(
            self, "Actores agregados",
            f"Se agregaron {len(nuevos)} al sector '{self._sector.nombre}':\n"
            f"{', '.join(nuevos)}\n\nLa próxima búsqueda los incluirá.")

    def _parametros(self) -> dict:
        rango = "todas las recientes"
        if self._desde and self._hasta:
            rango = f"{self._desde} a {self._hasta}"
        ambito = self._sector.ambito_geografico or ["Nacional"]
        return {
            "Sector": self._sector.nombre,
            "Descripción": self._sector.descripcion,
            "Ámbito geográfico": ambito,
            "Rango de fechas": rango,
            "Fecha de la búsqueda": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Versión de la app": __version__,
            "Consultas": self._sector.consultas,
        }

    def _exportar(self) -> None:
        self._sincronizar()
        mantenidas = [n for n in self._noticias if n.mantener]
        if not mantenidas:
            QMessageBox.information(self, "Nada para exportar",
                                    "No hay noticias marcadas para mantener.")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar resultado",
            f"noticias_{config._slug(self._sector.nombre)}.xlsx", "Excel (*.xlsx)")
        if not ruta:
            return
        export_excel(self._noticias, self._actores, ruta,
                     solo_mantenidas=True, parametros=self._parametros())
        QMessageBox.information(self, "Exportado", f"Guardado en:\n{ruta}")
