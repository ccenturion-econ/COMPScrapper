"""Pantalla inicial: elegir sector, opciones y rango de fechas; lanzar la búsqueda."""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from compscrapper import config
from compscrapper.models import Sector
from . import ayuda, estilo
from .editor_sector import EditorSector


class PaginaInicio(QWidget):
    iniciar_busqueda = Signal(object, bool, object, object)  # sector, descubrir, desde, hasta
    cancelar_busqueda = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        page = QVBoxLayout(self)
        page.setContentsMargins(16, 16, 16, 16)
        page.setSpacing(10)

        # -- Aviso de actualización (oculto salvo que haya versión nueva) --
        self.banner_update = QFrame()
        self.banner_update.setObjectName("update")
        self.banner_update.setVisible(False)
        ul = QHBoxLayout(self.banner_update)
        ul.setContentsMargins(12, 8, 12, 8)
        self.lbl_update = QLabel()
        self.lbl_update.setWordWrap(True)
        ul.addWidget(self.lbl_update, 1)
        self.btn_update = QPushButton("Descargar")
        self.btn_update.setObjectName("acento")
        self.btn_update.clicked.connect(self._abrir_descarga)
        ul.addWidget(self.btn_update)
        page.addWidget(self.banner_update)

        card = QFrame()
        card.setObjectName("card")
        page.addWidget(card)
        page.addStretch(1)
        outer = QVBoxLayout(card)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # -- Franja de encabezado con logo --
        header = QFrame()
        header.setObjectName("header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(18, 12, 18, 12)
        pm = estilo.logo_pixmap()
        if not pm.isNull():
            logo = QLabel()
            logo.setPixmap(pm.scaledToHeight(52, Qt.SmoothTransformation))
            hl.addWidget(logo)
            sep = QFrame()
            sep.setObjectName("sep")
            sep.setFrameShape(QFrame.VLine)
            hl.addWidget(sep)
        col = QVBoxLayout()
        col.setSpacing(0)
        titulo = QLabel("COMPScrapper")
        titulo.setStyleSheet(f"font-size: 19px; font-weight: 600; color: {estilo.TEXTO};")
        sub = QLabel("Monitor de competencia en noticias")
        sub.setStyleSheet(f"color: {estilo.SUAVE}; font-size: 12px;")
        col.addWidget(titulo)
        col.addWidget(sub)
        hl.addLayout(col)
        hl.addStretch(1)
        outer.addWidget(header)

        # -- Cuerpo de la tarjeta --
        body = QWidget()
        outer.addWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(14)

        # -- Sector --
        layout.addWidget(self._titulo_seccion("Sector"))
        fila_sector = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.setMinimumHeight(34)
        fila_sector.addWidget(self.combo, 1)
        self.btn_ia = QPushButton("\U0001F916  Crear con IA")  # 🤖 carita de robot
        self.btn_ia.setObjectName("acento")
        self.btn_ia.setMinimumHeight(34)
        fila_sector.addWidget(self.btn_ia)
        layout.addLayout(fila_sector)

        fila_gestion = QHBoxLayout()
        fila_gestion.setSpacing(6)
        self.btn_nuevo = QPushButton("Nuevo")
        self.btn_editar = QPushButton("Editar")
        self.btn_borrar = QPushButton("Borrar")
        self.btn_importar = QPushButton("Importar")
        self.btn_exportar = QPushButton("Exportar")
        for b in (self.btn_nuevo, self.btn_editar, self.btn_borrar,
                  self.btn_importar, self.btn_exportar):
            b.setObjectName("acento")
            fila_gestion.addWidget(b)
        fila_gestion.addStretch(1)
        layout.addLayout(fila_gestion)

        self.btn_nuevo.clicked.connect(self._nuevo)
        self.btn_ia.clicked.connect(self._crear_con_ia)
        self.btn_editar.clicked.connect(self._editar)
        self.btn_borrar.clicked.connect(self._borrar)
        self.btn_importar.clicked.connect(self._importar)
        self.btn_exportar.clicked.connect(self._exportar)

        # -- Opciones --
        opciones = QGroupBox("Opciones")
        ov = QVBoxLayout(opciones)
        self.chk_descubrir = QCheckBox("Descubrir actores del mercado")
        self.chk_descubrir.setChecked(True)
        self.chk_descubrir.setToolTip(ayuda.DESCUBRIR)
        ov.addWidget(self.chk_descubrir)

        self.chk_rango = QCheckBox("Limitar por rango de fechas")
        self.chk_rango.setToolTip(ayuda.RANGO_FECHAS)
        ov.addWidget(self.chk_rango)
        fila_fechas = QHBoxLayout()
        fila_fechas.addWidget(QLabel("Desde:"))
        self.fecha_desde = QDateEdit(QDate.currentDate().addMonths(-12))
        self.fecha_desde.setCalendarPopup(True)
        fila_fechas.addWidget(self.fecha_desde)
        fila_fechas.addWidget(QLabel("Hasta:"))
        self.fecha_hasta = QDateEdit(QDate.currentDate())
        self.fecha_hasta.setCalendarPopup(True)
        fila_fechas.addWidget(self.fecha_hasta)
        fila_fechas.addStretch(1)
        ov.addLayout(fila_fechas)
        self.chk_rango.toggled.connect(self._toggle_fechas)
        self._toggle_fechas(False)
        layout.addWidget(opciones)

        # -- Buscar / progreso --
        self.btn_buscar = QPushButton("Buscar")
        self.btn_buscar.setObjectName("primary")
        self.btn_buscar.setMinimumHeight(42)
        self.btn_buscar.clicked.connect(self._buscar)
        layout.addWidget(self.btn_buscar)

        self.barra = QProgressBar()
        self.barra.setVisible(False)
        self.barra.setTextVisible(True)
        layout.addWidget(self.barra)
        self.lbl_estado = QLabel("")
        layout.addWidget(self.lbl_estado)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setVisible(False)
        self.btn_cancelar.clicked.connect(self.cancelar_busqueda.emit)
        layout.addWidget(self.btn_cancelar)

        layout.addStretch(1)
        self.refrescar_sectores()

    def mostrar_actualizacion(self, info: dict) -> None:
        """Muestra el aviso de versión nueva con el botón de descarga."""
        self._url_descarga = info.get("url", "")
        self.lbl_update.setText(
            f"Hay una versión nueva disponible ({info.get('version', '')}). "
            "Descargala para actualizar.")
        self.banner_update.setVisible(True)

    def _abrir_descarga(self) -> None:
        url = getattr(self, "_url_descarga", "")
        if url:
            QDesktopServices.openUrl(QUrl(url))

    @staticmethod
    def _titulo_seccion(texto: str) -> QLabel:
        lbl = QLabel(texto)
        lbl.setStyleSheet(f"color: {estilo.SUAVE}; font-size: 12px; font-weight: 500;")
        return lbl

    # -- sectores --
    def refrescar_sectores(self, seleccionar: str | None = None) -> None:
        self.combo.clear()
        self.combo.addItems(config.list_sectors())
        if seleccionar:
            idx = self.combo.findText(seleccionar)
            if idx >= 0:
                self.combo.setCurrentIndex(idx)

    def _sector_seleccionado(self) -> Sector | None:
        nombre = self.combo.currentText()
        if not nombre:
            return None
        return config.load_sector(nombre)

    def _nuevo(self) -> None:
        dlg = EditorSector(parent=self)
        if dlg.exec():
            self.refrescar_sectores(dlg.sector_guardado.nombre)

    def _crear_con_ia(self) -> None:
        from .asistente_ia import AsistenteIA
        dlg = AsistenteIA(parent=self)
        if dlg.exec():
            self.refrescar_sectores(dlg.sector_creado.nombre)

    def _editar(self) -> None:
        sector = self._sector_seleccionado()
        if not sector:
            return
        dlg = EditorSector(sector, parent=self)
        if dlg.exec():
            self.refrescar_sectores(dlg.sector_guardado.nombre)

    def _borrar(self) -> None:
        nombre = self.combo.currentText()
        if not nombre:
            return
        if QMessageBox.question(self, "Borrar sector",
                                f"¿Borrar el sector '{nombre}'?") == QMessageBox.Yes:
            config.delete_sector(nombre)
            self.refrescar_sectores()

    def _importar(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(self, "Importar sector", "", "JSON (*.json)")
        if not ruta:
            return
        try:
            import json
            sector = Sector.from_dict(json.loads(open(ruta, encoding="utf-8").read()))
            config.save_sector(sector)
            self.refrescar_sectores(sector.nombre)
        except (ValueError, OSError) as e:
            QMessageBox.warning(self, "No se pudo importar", str(e))

    def _exportar(self) -> None:
        sector = self._sector_seleccionado()
        if not sector:
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar sector", f"{config._slug(sector.nombre)}.json", "JSON (*.json)")
        if not ruta:
            return
        import json
        open(ruta, "w", encoding="utf-8").write(
            json.dumps(sector.to_dict(), ensure_ascii=False, indent=2))

    # -- búsqueda --
    def _toggle_fechas(self, activo: bool) -> None:
        self.fecha_desde.setEnabled(activo)
        self.fecha_hasta.setEnabled(activo)

    def _buscar(self) -> None:
        sector = self._sector_seleccionado()
        if not sector:
            QMessageBox.information(self, "Sin sector",
                                    "Creá o elegí un sector antes de buscar.")
            return
        desde = hasta = None
        if self.chk_rango.isChecked():
            desde = self.fecha_desde.date().toPython()
            hasta = self.fecha_hasta.date().toPython()
        self.modo_busqueda(True)
        self.iniciar_busqueda.emit(sector, self.chk_descubrir.isChecked(), desde, hasta)

    def modo_busqueda(self, activo: bool) -> None:
        self.btn_buscar.setVisible(not activo)
        self.barra.setVisible(activo)
        self.btn_cancelar.setVisible(activo)
        if activo:
            self.barra.setRange(0, 0)  # indeterminada hasta el primer progreso
        else:
            self.lbl_estado.setText("")

    def actualizar_progreso(self, actual: int, total: int, mensaje: str) -> None:
        if total > 0:
            self.barra.setRange(0, total)
            self.barra.setValue(actual)
        self.lbl_estado.setText(mensaje)
