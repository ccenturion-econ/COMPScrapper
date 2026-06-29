"""Punto de entrada de la aplicación de escritorio.

    python -m gui.app
"""

from __future__ import annotations

import os
import sys

# Algunas instalaciones de PySide6 (p. ej. con el Python de CommandLineTools en
# macOS) no auto-configuran la ruta de sus plugins de plataforma, y Qt aborta con
# 'Could not find the Qt platform plugin ... in ""'. Se la indicamos explícitamente
# ANTES de importar cualquier módulo de Qt.
import PySide6  # noqa: E402

_QT_PLUGINS = os.path.join(os.path.dirname(PySide6.__file__), "Qt", "plugins")
if os.path.isdir(_QT_PLUGINS):
    os.environ.setdefault("QT_PLUGIN_PATH", _QT_PLUGINS)
    os.environ.setdefault(
        "QT_QPA_PLATFORM_PLUGIN_PATH", os.path.join(_QT_PLUGINS, "platforms")
    )

from PySide6.QtWidgets import QApplication  # noqa: E402

from compscrapper import config  # noqa: E402
from . import estilo  # noqa: E402
from .ventana_principal import VentanaPrincipal  # noqa: E402


def main() -> int:
    config.install_seed_sectors()  # instala el sector semilla la primera vez
    app = QApplication(sys.argv)
    app.setApplicationName("COMPScrapper")
    estilo.aplicar(app)  # hoja de estilos global + ícono
    ventana = VentanaPrincipal()
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
