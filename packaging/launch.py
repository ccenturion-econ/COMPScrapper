"""Punto de entrada para PyInstaller.

`gui/app.py` usa imports relativos (`from .ventana_principal import ...`), así que
no puede ser el script tope de PyInstaller (correría como `__main__` y los
relativos fallarían). Este lanzador importa el paquete `gui` y llama a main().
"""

import sys

from gui.app import main

if __name__ == "__main__":
    sys.exit(main())
