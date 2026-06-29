"""División geográfica de Paraguay (departamentos y ciudades/distritos).

Dataset incorporado, derivado de la codificación oficial DGEEC/INE (CNPV 2012).
Permite que el usuario acote la búsqueda a nivel subnacional: el ámbito elegido
se traduce en términos de lugar que el motor inyecta en las consultas, ya que el
RSS de Google News solo distingue la edición por país, no sub-regiones.

Convención de selección:
  - Nacional (todas las ciudades del país)  -> lista de términos vacía: sin
    restricción geográfica (la edición Paraguay ya cubre todo el país).
  - Un departamento completo                -> nombre del departamento + todas
    sus ciudades.
  - Ciudades puntuales                       -> esas ciudades.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_GEO_PATH = Path(__file__).resolve().parent / "data" / "paraguay_geo.json"


@lru_cache(maxsize=1)
def _data() -> dict:
    return json.loads(_GEO_PATH.read_text(encoding="utf-8"))


def fuente() -> str:
    return _data().get("fuente", "")


def departamentos() -> list[str]:
    """Nombres de los departamentos (incluye Asunción), en orden oficial."""
    return list(_data()["departamentos"].keys())


def ciudades(departamento: str) -> list[str]:
    """Ciudades/distritos de un departamento."""
    return list(_data()["departamentos"].get(departamento, []))


def resolver(seleccion: dict) -> list[str]:
    """Traduce una selección jerárquica a la lista plana de términos de lugar.

    `seleccion` admite:
      {"nacional": True}                          -> []  (todo el país)
      {"departamentos": ["Itapúa"]}               -> "Itapúa" + sus ciudades
      {"ciudades": ["Encarnación", "Hohenau"]}    -> esas ciudades
    Las claves se pueden combinar; el resultado se deduplica preservando orden.
    """
    if seleccion.get("nacional"):
        return []
    terminos: list[str] = []
    for dep in seleccion.get("departamentos", []):
        terminos.append(dep)
        terminos.extend(ciudades(dep))
    terminos.extend(seleccion.get("ciudades", []))
    vistos = set()
    unicos = []
    for t in terminos:
        if t and t not in vistos:
            vistos.add(t)
            unicos.append(t)
    return unicos
