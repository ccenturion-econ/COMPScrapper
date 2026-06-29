"""Chequeo de actualización contra los releases del repo público en GitHub.

Sin interfaz. Consulta el último release publicado y compara la versión (semver).
Si algo falla (sin red, sin releases, error), devuelve None: la app simplemente
no muestra el aviso. La descarga es manual (aviso + botón); no hay autoupdate.
"""

from __future__ import annotations

import re
from typing import Optional

import requests

REPO = "ccenturion-econ/COMPScrapper"
_API = f"https://api.github.com/repos/{REPO}/releases/latest"
_RELEASES_URL = f"https://github.com/{REPO}/releases/latest"


def _version_tupla(texto: str) -> tuple[int, ...]:
    """'v1.2.3' / '1.2' -> (1,2,3) / (1,2). Vacío -> (0,)."""
    nums = re.findall(r"\d+", texto or "")
    return tuple(int(n) for n in nums[:3]) if nums else (0,)


def buscar_actualizacion(version_actual: str, timeout: int = 6, session=None) -> Optional[dict]:
    """Devuelve {version, nombre, url} si hay un release más nuevo que `version_actual`.

    Devuelve None si no hay actualización, no hay red, no hay releases, o no se
    pudo verificar. Nunca lanza: el aviso es opcional.
    """
    try:
        cliente = session or requests
        r = cliente.get(_API, timeout=timeout,
                        headers={"Accept": "application/vnd.github+json"})
        if r.status_code != 200:
            return None
        data = r.json()
        tag = data.get("tag_name") or ""
        if _version_tupla(tag) > _version_tupla(version_actual):
            return {
                "version": tag,
                "nombre": data.get("name") or tag,
                "url": data.get("html_url") or _RELEASES_URL,
            }
    except (requests.RequestException, ValueError):
        return None
    return None
