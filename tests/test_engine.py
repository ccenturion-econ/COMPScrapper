"""Pruebas del motor: funciones puras (sin red, deterministas) sobre entradas fijas.

Verifican el comportamiento vigente del scoring por niveles, el matcheo tolerante
a género/número, el resaltado de enlaces y el descubrimiento de actores. Son
autónomas: no dependen de servicios externos.

Ejecutable directo:  python tests/test_engine.py
O con pytest:        pytest
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from compscrapper import engine as eng  # noqa: E402
from compscrapper.models import Sector  # noqa: E402


def test_strip_accents():
    assert eng.strip_accents("ASOCIACIÓN") == "ASOCIACION"
    assert eng.strip_accents("Ñandú") == "Nandu"
    assert eng.strip_accents("sin acentos") == "sin acentos"


def test_matcheo_variantes():
    """Singular/plural y masculino/femenino valen igual; no debe haber
    derivaciones falsas (precio≠precioso, compra≠comprar)."""
    s = Sector.from_dict({
        "nombre": "t", "consultas": ["x"],
        "terminos_sector": ["frigorífico, ganado, carne"],
        "terminos_queja": ["denuncia"],
        "terminos_contexto": ["precio, compra, exportación"],
    })

    def halla(titulo):
        _, terms = eng.score_relevance(titulo, s)
        return set(terms)

    assert "frigorífico" in halla("Los frigoríficos elevan precios")     # plural
    assert "exportación" in halla("Crecen las exportaciones de carne")   # -ción/-ciones
    assert "carne" in halla("Suben las carnes y la denuncia avanza")     # plural
    # sin falsos positivos por derivación:
    assert "precio" not in halla("Un paisaje precioso en el campo")
    assert "compra" not in halla("Van a comprar maquinaria")


def test_regla_relevancia():
    """El SECTOR es obligatorio (sin mención del mercado la nota se descarta).
    Dado el sector: 3 = +queja+contexto; 2 = +queja; 1 = +contexto; 0 = el resto.
    """
    def _nivel(*, sector=False, queja=False, contexto=False):
        s = Sector.from_dict({
            "nombre": "t",
            "terminos_sector": ["sectorpalabra"],
            "terminos_queja": ["quejapalabra"],
            "terminos_contexto": ["contextopalabra"],
            "consultas": ["x"],
        })
        partes = []
        if sector:
            partes.append("sectorpalabra")
        if queja:
            partes.append("quejapalabra")
        if contexto:
            partes.append("contextopalabra")
        nivel, _ = eng.score_relevance(" ".join(partes) or "nada", s)
        return nivel

    assert _nivel(sector=True, queja=True, contexto=True) == 3
    assert _nivel(sector=True, queja=True) == 2
    assert _nivel(sector=True, contexto=True) == 1
    assert _nivel(queja=True, contexto=True) == 0    # sin sector: descartada (ruido)
    assert _nivel(sector=True) == 0                  # solo sector: insuficiente
    assert _nivel(queja=True) == 0
    assert _nivel() == 0


def test_highlight_url():
    url = "https://www.example.com/nota"
    # Sin términos, no hay fragmento.
    assert eng.highlight_url(url, "Cualquier título", []) == ""
    # Resalta la variante real que aparece en el título (no el término del
    # diccionario): término "frigorífico" -> resalta "frigoríficos".
    out = eng.highlight_url(url, "Los frigoríficos elevan precios", ["frigorífico"])
    assert out.startswith(url + "#:~:text=")
    assert quote("frigoríficos", safe="") in out


def test_extract_actor_candidates():
    """Detecta organizaciones (gremio, cámara, empresa S.A.) que aparecen en 2+ notas."""
    textos = [
        ("La Cámara de Productores se reunió. Frigorífico Ejemplo S.A. participó del llamado.", "n1"),
        ("La Cámara de Productores insistió. Frigorífico Ejemplo S.A. respondió a la consulta.", "n2"),
    ]
    acts = {a.candidato for a in eng.extract_actor_candidates(textos, ["carne"], [])}
    assert any("Cámara de Productores" in a for a in acts)
    assert any("Frigorífico Ejemplo" in a for a in acts)


def test_actores_no_palabras_comunes():
    """El descubrimiento no debe tomar palabras comunes en mayúsculas como siglas.
    Tres reglas: acento (CÓMO/AFECTARÍA), lista de comunes, y la prueba de corpus
    (una palabra que aparece en minúscula no es sigla — CEMENTO). Una sigla real
    sin acento (INTN) sí pasa."""
    textos = [
        ("¿CÓMO AFECTARÍA esto? El CEMENTO escasea y la INTN investiga el sector.", "t1"),
        ("Otra nota: ¿CÓMO AFECTARÍA? El cemento sube; la INTN vuelve a opinar.", "t2"),
    ]
    acts = {a.candidato for a in eng.extract_actor_candidates(textos, ["sector"], [])}
    assert "CÓMO" not in acts and "AFECTARÍA" not in acts   # acento
    assert "CEMENTO" not in acts   # aparece como "cemento" en minúscula: no es sigla
    assert "INTN" in acts          # sigla real, solo en mayúsculas


def test_clean_candidate():
    assert eng._clean_candidate("Cooperativa de") == "Cooperativa"
    assert eng._clean_candidate("Cámara de Productores y") == "Cámara de Productores"
    assert eng._clean_candidate("Frigorífico Ejemplo SA") == "Frigorífico Ejemplo SA"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(fns)} pruebas del motor pasaron.")
