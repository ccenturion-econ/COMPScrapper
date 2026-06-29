"""Interfaz gráfica (PySide6) de COMPScrapper.

El motor (`compscrapper/`) no conoce Qt; la GUI lo corre en un hilo aparte
(`worker.py`) y traduce los callbacks de progreso/cancelación a señales Qt.
"""
