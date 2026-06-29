"""Asistente de IA para crear sectores (la app NO llama a ninguna IA).

Provee dos cosas para el flujo "describir el mercado -> pegar el JSON que devuelve
la IA del usuario":
  - build_prompt(descripcion): arma el texto a pegar en ChatGPT/Claude/etc.
  - sector_desde_texto_ia(texto): extrae y valida el JSON que la IA devolvió,
    tolerando texto o fences ```json alrededor, y construye un Sector.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Sector

_PROMPT_FILE = Path(__file__).resolve().parent / "data" / "prompt_sector.txt"


def build_prompt(descripcion: str) -> str:
    """Texto listo para pegar en una IA, con la descripción del usuario incrustada."""
    plantilla = _PROMPT_FILE.read_text(encoding="utf-8")
    desc = descripcion.strip() or "(describí tu mercado acá)"
    return plantilla.replace("{descripcion}", desc)


def _extraer_json(texto: str) -> str:
    """Devuelve el primer objeto JSON balanceado dentro de `texto`.

    Tolera fences de código (```json ... ```) y texto explicativo antes o después:
    recorre desde la primera '{' y corta en la llave que la cierra, respetando
    llaves dentro de cadenas y caracteres escapados.
    """
    inicio = texto.find("{")
    if inicio == -1:
        raise ValueError("No encontré un objeto JSON en el texto pegado.")
    profundidad = 0
    en_cadena = False
    escape = False
    for i in range(inicio, len(texto)):
        c = texto[i]
        if en_cadena:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                en_cadena = False
            continue
        if c == '"':
            en_cadena = True
        elif c == "{":
            profundidad += 1
        elif c == "}":
            profundidad -= 1
            if profundidad == 0:
                return texto[inicio:i + 1]
    raise ValueError("El JSON está incompleto: falta cerrar una llave '}'.")


def sector_desde_texto_ia(texto: str) -> Sector:
    """Parsea la respuesta de la IA y construye un Sector validado.

    Lanza ValueError con un mensaje en español si el texto no trae un JSON válido
    o si no cumple el esquema del sector.
    """
    if not texto or not texto.strip():
        raise ValueError("Pegá la respuesta de la IA (el JSON del sector).")
    fragmento = _extraer_json(texto)
    try:
        data = json.loads(fragmento)
    except json.JSONDecodeError as e:
        raise ValueError(f"El JSON tiene un error de formato: {e.msg} (línea {e.lineno}).") from e
    return Sector.from_dict(data)  # valida tipos y campos; puede lanzar ValueError
