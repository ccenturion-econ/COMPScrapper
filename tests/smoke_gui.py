"""Smoke de construcción de la interfaz, sin pantalla (Qt offscreen).

No reemplaza una prueba visual; verifica que los widgets se construyen, que el
selector geográfico resuelve y que la tabla de resultados vuelca su estado.

    QT_QPA_PLATFORM=offscreen python tests/smoke_gui.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

from compscrapper.models import Noticia, Sector  # noqa: E402

app = QApplication.instance() or QApplication([])

from gui.ventana_principal import VentanaPrincipal  # noqa: E402
from gui.editor_sector import EditorSector  # noqa: E402
from gui.selector_geografico import SelectorGeografico  # noqa: E402

# 1) Ventana principal construye.
v = VentanaPrincipal()
assert v.stack.count() == 2
print("OK  ventana principal")

# 2) Selector geográfico: nacional -> [], y reconstrucción de una selección.
sel = SelectorGeografico()
assert sel.ambito() == []
sel.set_ambito(["Itapúa"])
amb = sel.ambito()
assert "Itapúa" in amb and "Encarnación" in amb
print("OK  selector geográfico (depto completo ->", len(amb), "términos)")

# 3) Editor: cargar un sector y releerlo.
s = Sector(nombre="Prueba", descripcion="d",
           terminos_sector=["carne"], terminos_queja=["denuncia"],
           terminos_contexto=["licitacion"], consultas=["carne denuncia"],
           ambito_geografico=["Encarnación"], exclusiones=["feria"])
ed = EditorSector(s)
releido = ed.sector_actual()
assert releido.nombre == "Prueba"
assert releido.terminos_contexto == ["licitacion"]
assert "Encarnación" in releido.ambito_geografico
print("OK  editor de sector (ida y vuelta)")

# 4) Resultados: mostrar, sincronizar filtro manual.
noticias = [
    Noticia(3, "A", "Diario", ["carne"], None, "https://x.com/a", "", "q", True),
    Noticia(2, "B", "Diario", ["precio"], None, "https://x.com/b", "", "q", True),
]
v.resultados.mostrar(noticias, [], s, None, None)
v.resultados.tabla.item(1, 0).setCheckState(v.resultados.tabla.item(1, 0).checkState().Unchecked)
v.resultados._sincronizar()
assert noticias[0].mantener is True and noticias[1].mantener is False
assert v.resultados.banner.isVisible()  # sector con 'licitacion' -> sugerencia
print("OK  resultados (filtro manual + banner de contrataciones)")

print("\nSmoke de GUI: todo construyó y respondió.")
