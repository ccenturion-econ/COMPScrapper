"""Worker que corre el motor en un hilo aparte, sin congelar la ventana.

Traduce los callbacks del motor (progreso/cancelación) a señales Qt. La
cancelación usa un threading.Event que se setea desde el hilo de la interfaz y
el motor consulta entre pedidos.
"""

from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal

from compscrapper.engine import BusquedaCancelada, NewsEngine
from compscrapper.models import Progreso, Sector


class BusquedaWorker(QObject):
    progreso = Signal(int, int, str)        # actual, total, mensaje
    terminado = Signal(list, list)          # noticias, actores
    error = Signal(str)
    cancelado = Signal()

    def __init__(self, sector: Sector, descubrir: bool, desde=None, hasta=None):
        super().__init__()
        self._sector = sector
        self._descubrir = descubrir
        self._desde = desde
        self._hasta = hasta
        self._cancel = threading.Event()

    def cancelar(self) -> None:
        self._cancel.set()

    def run(self) -> None:
        def on_progress(p: Progreso) -> None:
            self.progreso.emit(p.actual, p.total, p.mensaje)

        try:
            engine = NewsEngine()
            noticias, actores = engine.buscar(
                self._sector,
                descubrir=self._descubrir,
                desde=self._desde,
                hasta=self._hasta,
                on_progress=on_progress,
                should_cancel=self._cancel.is_set,
            )
            self.terminado.emit(noticias, actores)
        except BusquedaCancelada:
            self.cancelado.emit()
        except Exception as e:  # noqa: BLE001 - cualquier fallo se reporta a la UI
            self.error.emit(str(e))
