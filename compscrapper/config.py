"""Persistencia de sectores como archivos JSON en la carpeta de datos del SO.

Los sectores son *datos*, no código: se cargan con json.load y se validan por
tipos en Sector.from_dict. Nunca se ejecuta contenido del archivo.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from pathlib import Path

from .models import Sector

APP_NAME = "COMPScrapper"

# Datos incorporados al paquete (viajan en el bundle de PyInstaller).
_PKG_DATA = Path(__file__).resolve().parent / "data"
_SEED_DIR = _PKG_DATA / "sectores_semilla"
_SEED_MARKER = ".semillas_instaladas"


def archivo_datos(nombre: str) -> Path:
    """Ruta a un archivo de datos incorporado (logo, prompt, geografía...)."""
    return _PKG_DATA / nombre


def app_data_dir() -> Path:
    """Carpeta de datos del usuario, según el sistema operativo."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:  # Linux y otros
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / APP_NAME


def sectors_dir() -> Path:
    d = app_data_dir() / "sectores"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _slug(nombre: str) -> str:
    """Nombre de archivo seguro (ASCII, sin acentos) a partir del nombre del sector."""
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFD", nombre.lower().strip())
        if unicodedata.category(c) != "Mn"
    )
    s = "".join(c for c in sin_acentos if c.isalnum() or c in (" ", "-", "_"))
    s = re.sub(r"[\s]+", "_", s).strip("_")
    return s or "sector"


def sector_path(nombre: str) -> Path:
    return sectors_dir() / f"{_slug(nombre)}.json"


def list_sectors() -> list[str]:
    """Nombres de sectores guardados, ordenados alfabéticamente."""
    nombres = []
    for path in sectors_dir().glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            nombre = data.get("nombre")
            if isinstance(nombre, str) and nombre.strip():
                nombres.append(nombre.strip())
        except (json.JSONDecodeError, OSError):
            continue
    return sorted(nombres, key=str.lower)


def load_sector(nombre: str) -> Sector:
    path = sector_path(nombre)
    if not path.exists():
        raise FileNotFoundError(f"No existe el sector '{nombre}'.")
    data = json.loads(path.read_text(encoding="utf-8"))
    return Sector.from_dict(data)


def save_sector(sector: Sector) -> Path:
    path = sector_path(sector.nombre)
    path.write_text(
        json.dumps(sector.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def delete_sector(nombre: str) -> None:
    path = sector_path(nombre)
    if path.exists():
        path.unlink()


def install_seed_sectors() -> list[str]:
    """Copia los sectores semilla incorporados a la carpeta del usuario, una sola vez.

    Idempotente: tras la primera instalación deja un marcador y no vuelve a copiar,
    de modo que respeta los sectores que el usuario haya editado o borrado. Tampoco
    pisa un sector existente con el mismo nombre de archivo.
    """
    marker = app_data_dir() / _SEED_MARKER
    if marker.exists() or not _SEED_DIR.is_dir():
        return []

    instalados = []
    for semilla in sorted(_SEED_DIR.glob("*.json")):
        try:
            data = json.loads(semilla.read_text(encoding="utf-8"))
            sector = Sector.from_dict(data)  # valida antes de instalar
        except (json.JSONDecodeError, OSError, ValueError):
            continue
        destino = sector_path(sector.nombre)
        if not destino.exists():
            save_sector(sector)
            instalados.append(sector.nombre)

    app_data_dir().mkdir(parents=True, exist_ok=True)
    marker.write_text("", encoding="utf-8")
    return instalados
