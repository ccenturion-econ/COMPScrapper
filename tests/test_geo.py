"""División geográfica y expansión geográfica de consultas.

Ejecutable directo:  python tests/test_geo.py
O con pytest:        pytest
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from compscrapper import geo  # noqa: E402
from compscrapper.engine import expand_queries, geo_batches  # noqa: E402


def test_dataset():
    deps = geo.departamentos()
    assert len(deps) == 18  # 17 departamentos + Asunción
    assert "Itapúa" in deps and "Central" in deps and "Asunción" in deps
    assert "Encarnación" in geo.ciudades("Itapúa")
    assert "Ciudad del Este" in geo.ciudades("Alto Paraná")


def test_resolver():
    assert geo.resolver({"nacional": True}) == []
    itapua = geo.resolver({"departamentos": ["Itapúa"]})
    assert itapua[0] == "Itapúa"  # el departamento encabeza
    assert "Encarnación" in itapua
    assert geo.resolver({"ciudades": ["Hohenau", "Encarnación"]}) == ["Hohenau", "Encarnación"]


def test_expand_nacional_ancla_pais():
    # Ámbito vacío = Nacional: ancla cada consulta al grupo país (términos +
    # dominios de medios), en un único grupo OR sin lotear, porque la edición
    # gl=PY de Google News no restringe los resultados a Paraguay.
    from compscrapper.engine import GEO_NACIONAL
    out = expand_queries(["carne denuncia"], [])
    assert len(out) == 1  # una sola consulta por base: el ancla no se lotea
    grupo = " OR ".join(GEO_NACIONAL)
    assert out[0] == f"carne denuncia ({grupo})"
    assert "site:abc.com.py" in out[0] and "Paraguay" in out[0]


def test_expand_dominios_sector_nacional():
    # Los dominios del sector se suman como site: al grupo país, en la misma
    # consulta (no multiplican consultas).
    out = expand_queries(["carne"], [], dominios_sector=["arp.org.py", "site:capasu.org.py"])
    assert len(out) == 1
    assert "site:arp.org.py" in out[0]      # se le agrega el prefijo
    assert "site:capasu.org.py" in out[0]   # idempotente si ya lo trae
    assert "Paraguay" in out[0]             # sigue el ancla de país


def test_expand_dominios_sector_subnacional():
    # En subnacional, los dominios del sector se OR-ean al grupo de localidades.
    out = expand_queries(["carne"], ["Encarnación"], dominios_sector=["arp.org.py"])
    assert out == ['carne (Encarnación OR site:arp.org.py)']


def test_expand_pocas_localidades():
    # los multipalabra van entre comillas; los de una palabra no.
    out = expand_queries(["carne denuncia"], ["Ciudad del Este", "Hernandarias"])
    assert out == ['carne denuncia ("Ciudad del Este" OR Hernandarias)']


def test_expand_muchas_localidades_se_lotea():
    ciudades = [f"Ciudad{i}" for i in range(30)]
    batches = geo_batches(ciudades, max_or=12)
    assert [len(b) for b in batches] == [12, 12, 6]
    out = expand_queries(["q"], ciudades, max_or=12)
    assert len(out) == 3  # una consulta base x 3 lotes


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(fns)} pruebas de geografía pasaron.")
