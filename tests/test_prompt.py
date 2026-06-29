"""Pruebas del asistente de IA: armado del prompt y parseo del JSON devuelto."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compscrapper.prompt import build_prompt, sector_desde_texto_ia  # noqa: E402

_SECTOR_OK = """{
  "nombre": "Combustibles",
  "terminos_sector": ["estación de servicio", "combustible", "nafta"],
  "terminos_queja": ["acuerdo", "cartel", "colusión"],
  "terminos_contexto": ["precio"],
  "consultas": ["combustibles acuerdo de precios"]
}"""


def test_build_prompt_incrusta_descripcion():
    p = build_prompt("Combustibles en Paraguay")
    assert "Combustibles en Paraguay" in p
    assert "{descripcion}" not in p  # el marcador se reemplazó
    assert "terminos_queja" in p     # trae el esquema


def test_build_prompt_descripcion_vacia():
    p = build_prompt("   ")
    assert "describí tu mercado" in p.lower()


def test_parse_json_limpio():
    s = sector_desde_texto_ia(_SECTOR_OK)
    assert s.nombre == "Combustibles"
    assert "nafta" in s.terminos_sector


def test_parse_con_fences_y_texto_alrededor():
    texto = "¡Claro! Acá está tu sector:\n```json\n" + _SECTOR_OK + "\n```\nEspero que sirva."
    s = sector_desde_texto_ia(texto)
    assert s.nombre == "Combustibles"


def test_parse_respeta_llaves_dentro_de_cadenas():
    texto = 'blah {"nombre": "X {raro}", "consultas": ["a"], "terminos_sector": ["y"]} fin'
    s = sector_desde_texto_ia(texto)
    assert s.nombre == "X {raro}"


def test_parse_sin_json():
    try:
        sector_desde_texto_ia("la IA no devolvió nada útil")
        assert False, "debió lanzar ValueError"
    except ValueError as e:
        assert "JSON" in str(e)


def test_parse_json_incompleto():
    try:
        sector_desde_texto_ia('{"nombre": "X", "consultas": ["a"]')  # falta cerrar
        assert False, "debió lanzar ValueError"
    except ValueError as e:
        assert "llave" in str(e).lower() or "json" in str(e).lower()


def test_parse_vacio():
    try:
        sector_desde_texto_ia("   ")
        assert False
    except ValueError:
        pass


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(fns)} pruebas del asistente pasaron.")
