"""Carga/guardado/validación de sectores JSON, sin tocar la carpeta real del usuario.

Ejecutable directo:  python tests/test_config.py
O con pytest:        pytest
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from compscrapper import config  # noqa: E402
from compscrapper.models import Sector  # noqa: E402


def _redirigir_a_temp(tmp: Path):
    config.app_data_dir = lambda: tmp  # type: ignore[assignment]


def test_round_trip(tmp_path: Path):
    _redirigir_a_temp(tmp_path)
    sector = Sector(
        nombre="Café / Región Este",
        descripcion="prueba",
        terminos_sector=["café", "cafetalero"],
        terminos_queja=["denuncia", "competencia"],
        terminos_contexto=["precio", "exportación"],
        consultas=['café precio Paraguay'],
        consultas_descubrimiento=["gremios cafetaleros Paraguay"],
        ambito_geografico=["Itapúa", "Encarnación"],
        exclusiones=["cosecha"],
    )
    config.save_sector(sector)
    assert "Café / Región Este" in config.list_sectors()
    cargado = config.load_sector("Café / Región Este")
    assert cargado.to_dict() == sector.to_dict()
    config.delete_sector("Café / Región Este")
    assert config.list_sectors() == []


def test_validacion_rechaza_basura():
    for malo in [
        {"nombre": ""},
        {"nombre": "x", "terminos_sector": "no es lista"},
        {"nombre": "x", "consultas": [1, 2, 3]},
        "no es un objeto",
    ]:
        try:
            Sector.from_dict(malo)  # type: ignore[arg-type]
            raise AssertionError(f"debió rechazar: {malo!r}")
        except ValueError:
            pass


def test_slug_seguro():
    assert config._slug("Café / Región Este") == "cafe_region_este"
    assert config._slug("../../etc/passwd") == "etcpasswd"
    assert config._slug("") == "sector"


def test_semilla_carne(tmp_path: Path):
    _redirigir_a_temp(tmp_path)
    instalados = config.install_seed_sectors()
    assert "Carne" in instalados
    car = config.load_sector("Carne")
    assert car.terminos_sector and car.terminos_queja and car.consultas
    # idempotente: segunda llamada no reinstala nada.
    assert config.install_seed_sectors() == []
    # respeta el borrado del usuario: no reaparece tras borrarla.
    config.delete_sector("Carne")
    assert config.install_seed_sectors() == []
    assert "Carne" not in config.list_sectors()


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        test_round_trip(Path(d))
        print("OK  test_round_trip")
    test_validacion_rechaza_basura()
    print("OK  test_validacion_rechaza_basura")
    test_slug_seguro()
    print("OK  test_slug_seguro")
    with tempfile.TemporaryDirectory() as d:
        test_semilla_carne(Path(d))
        print("OK  test_semilla_carne")
    print("\n4 pruebas de configuración pasaron.")
