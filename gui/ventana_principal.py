"""Ventana principal: orquesta las pantallas y el hilo de búsqueda."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget

from .pagina_inicio import PaginaInicio
from .pagina_resultados import PaginaResultados
from .worker import BusquedaWorker


class _ChequeoVersion(QObject):
    """Consulta en segundo plano si hay una versión más nueva en GitHub."""

    listo = Signal(object)  # dict con la info, o None

    def run(self) -> None:
        from compscrapper import __version__
        from compscrapper.update import buscar_actualizacion
        self.listo.emit(buscar_actualizacion(__version__))


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("COMPScrapper")
        self.resize(880, 660)
        self.setMinimumSize(720, 560)

        self.stack = QStackedWidget()
        self.inicio = PaginaInicio()
        self.resultados = PaginaResultados()
        self.stack.addWidget(self.inicio)       # 0
        self.stack.addWidget(self.resultados)   # 1
        self.setCentralWidget(self.stack)

        self.inicio.iniciar_busqueda.connect(self._iniciar)
        self.inicio.cancelar_busqueda.connect(self._cancelar)
        self.resultados.volver.connect(lambda: self.stack.setCurrentIndex(0))

        self._thread = None
        self._worker = None
        self._params = None

        self._verificar_actualizacion()

    def _verificar_actualizacion(self) -> None:
        # Hilo daemon: una sola consulta de red; no bloquea el cierre de la app.
        # El worker vive en el hilo principal, así que su señal `listo` se entrega
        # de forma segura a la GUI (conexión en cola entre hilos).
        import threading
        self._upd_worker = _ChequeoVersion()
        self._upd_worker.listo.connect(self._on_version)
        threading.Thread(target=self._upd_worker.run, daemon=True).start()

    def _on_version(self, info) -> None:
        if info:
            self.inicio.mostrar_actualizacion(info)

    def _iniciar(self, sector, descubrir, desde, hasta) -> None:
        self._params = (sector, desde, hasta)
        self._thread = QThread(self)
        self._worker = BusquedaWorker(sector, descubrir, desde, hasta)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progreso.connect(self.inicio.actualizar_progreso)
        self._worker.terminado.connect(self._terminado)
        self._worker.error.connect(self._error)
        self._worker.cancelado.connect(self._cancelado)
        for sig in (self._worker.terminado, self._worker.error, self._worker.cancelado):
            sig.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.start()

    def _cancelar(self) -> None:
        if self._worker:
            self._worker.cancelar()
            self.inicio.lbl_estado.setText("Cancelando...")

    def _terminado(self, noticias, actores) -> None:
        self.inicio.modo_busqueda(False)
        sector, desde, hasta = self._params
        self.resultados.mostrar(noticias, actores, sector, desde, hasta)
        self.stack.setCurrentIndex(1)

    def _error(self, mensaje) -> None:
        self.inicio.modo_busqueda(False)
        QMessageBox.critical(self, "Error en la búsqueda", mensaje)

    def _cancelado(self) -> None:
        self.inicio.modo_busqueda(False)
        self.inicio.lbl_estado.setText("Búsqueda cancelada.")
