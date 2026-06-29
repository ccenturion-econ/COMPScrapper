"""Pruebas del chequeo de actualización (sin red, con sesión falsa)."""

from __future__ import annotations

import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compscrapper.update import buscar_actualizacion  # noqa: E402


class _Resp:
    def __init__(self, status, data=None):
        self.status_code = status
        self._data = data or {}

    def json(self):
        return self._data


class _Sesion:
    def __init__(self, resp):
        self._resp = resp

    def get(self, url, **kw):
        return self._resp


def test_hay_version_nueva():
    s = _Sesion(_Resp(200, {"tag_name": "v0.2.0", "name": "0.2", "html_url": "http://x"}))
    info = buscar_actualizacion("0.1.0", session=s)
    assert info and info["version"] == "v0.2.0" and info["url"] == "http://x"


def test_misma_version():
    s = _Sesion(_Resp(200, {"tag_name": "v0.1.0"}))
    assert buscar_actualizacion("0.1.0", session=s) is None


def test_version_anterior():
    s = _Sesion(_Resp(200, {"tag_name": "v0.0.9"}))
    assert buscar_actualizacion("0.1.0", session=s) is None


def test_semver_numerico():
    # 0.10.0 es más nuevo que 0.9.0 (comparación numérica, no de texto)
    s = _Sesion(_Resp(200, {"tag_name": "v0.10.0"}))
    assert buscar_actualizacion("0.9.0", session=s)


def test_sin_releases_404():
    assert buscar_actualizacion("0.1.0", session=_Sesion(_Resp(404))) is None


def test_error_de_red():
    class _SesionErr:
        def get(self, *a, **k):
            raise requests.RequestException("sin red")
    assert buscar_actualizacion("0.1.0", session=_SesionErr()) is None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(fns)} pruebas de actualización pasaron.")
