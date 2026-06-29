"""CLI delgada: conserva el uso por terminal sobre el mismo motor que la GUI.

    python -m compscrapper.cli --listar
    python -m compscrapper.cli --sector "carne" [--no-descubrir] [--salida out.xlsx]
    python -m compscrapper.cli --importar ruta/al/sector.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from . import __version__, config
from .engine import NewsEngine
from .export import export_excel
from .models import Sector
from .suggest import MENSAJE_SUGERENCIA, es_relacionado_contrataciones

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("compscrapper")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=f"COMPScrapper {__version__}")
    parser.add_argument("--listar", action="store_true", help="Listar sectores guardados")
    parser.add_argument("--sector", help="Nombre del sector a monitorear")
    parser.add_argument("--no-descubrir", action="store_true", help="Omitir descubrimiento de actores")
    parser.add_argument("--salida", help="Ruta del Excel de salida")
    parser.add_argument("--importar", help="Importar un sector desde un archivo JSON")
    args = parser.parse_args(argv)

    nuevos = config.install_seed_sectors()
    if nuevos:
        logger.info("Sectores semilla instalados: %s", ", ".join(nuevos))

    if args.importar:
        data = json.loads(open(args.importar, encoding="utf-8").read())
        sector = Sector.from_dict(data)
        path = config.save_sector(sector)
        logger.info("Sector '%s' guardado en %s", sector.nombre, path)
        return 0

    if args.listar:
        nombres = config.list_sectors()
        if not nombres:
            logger.info("No hay sectores guardados en %s", config.sectors_dir())
        for nombre in nombres:
            print(f"  {nombre}")
        return 0

    if not args.sector:
        parser.error("Indicá --sector, --listar o --importar.")

    sector = config.load_sector(args.sector)
    logger.info("Sector '%s': %s", sector.nombre, sector.descripcion)
    if es_relacionado_contrataciones(sector):
        logger.info(MENSAJE_SUGERENCIA)

    def on_progress(p):
        logger.info("[%s %d/%d] %s", p.fase, p.actual, p.total, p.mensaje)

    engine = NewsEngine()
    noticias, actores = engine.buscar(
        sector, descubrir=not args.no_descubrir, on_progress=on_progress
    )
    n_top = sum(1 for n in noticias if n.relevancia == 3)
    logger.info("Noticias: %d (relevancia 3: %d) | actores candidatos: %d",
                len(noticias), n_top, len(actores))

    if noticias or actores:
        salida = args.salida or f"noticias_{config._slug(sector.nombre)}.xlsx"
        export_excel(noticias, actores, salida, solo_mantenidas=False)
        logger.info("✓ Guardado en %s", salida)
    else:
        logger.warning("No se encontraron resultados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
