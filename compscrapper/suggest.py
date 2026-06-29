"""Detección de contexto 'contrataciones públicas'.

Si un sector apunta a compras/licitaciones públicas, la interfaz muestra un aviso
sugiriendo complementar el análisis con herramientas específicas de detección de
indicios de colusión en contrataciones.
"""

from __future__ import annotations

import re
import unicodedata

from .models import Sector

_PROCUREMENT_TERMS = [
    "licitacion", "licitaciones", "contratacion", "contrataciones", "dncp",
    "adjudicacion", "adjudican", "adjudicada", "adjudicadas", "pliego",
    "compra publica", "compras publicas", "oferente", "oferentes",
    "proveedor del estado", "contrato publico", "subasta",
]

MENSAJE_SUGERENCIA = (
    "Esta búsqueda está relacionada con contrataciones públicas. Considerá "
    "complementarla con herramientas específicas de detección de indicios de "
    "prácticas anticompetitivas en licitaciones públicas."
)


def _norm(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    )


def es_relacionado_contrataciones(sector: Sector) -> bool:
    """True si los términos o consultas del sector evocan compras públicas."""
    blob = _norm(
        " ".join(
            sector.terminos_contexto
            + sector.consultas
            + sector.consultas_descubrimiento
        )
    )
    return any(
        re.search(r"\b" + re.escape(_norm(term)) + r"\b", blob)
        for term in _PROCUREMENT_TERMS
    )
