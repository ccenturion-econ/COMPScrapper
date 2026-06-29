# COMPScrapper

Aplicación de escritorio (Mac y Windows) para monitorear noticias sectoriales y detectar
problemas de competencia en cualquier mercado nacional o subnacional de Paraguay. El
ámbito de cada búsqueda se define al configurar el sector. Incluye un asistente que arma un
prompt para crear el sector con ayuda de una IA externa, a partir de su descripción y el
problema de competencia a monitorear. Pensada para usarse sin conocimientos de código: se
cargan los parámetros en una pantalla, se filtran manualmente las noticias encontradas y se
exporta un Excel.

## Instalar

Descargá el instalador de la [página de versiones (Releases)](https://github.com/ccenturion-econ/COMPScrapper/releases)
y seguí la **[guía de instalación](INSTALACION.md)** (cómo abrirla la primera vez en
macOS y Windows, ya que la app todavía no está firmada).

## Estado

- **Motor (`compscrapper/`):** búsqueda en Google News con ancla de país, relevancia por
  niveles (sector + queja/competencia + contexto), descubrimiento de actores, exportación
  a Excel y CLI. Cubierto por pruebas.
- **Interfaz (PySide6):** inicio → buscar (con progreso/cancelar en un hilo) → resultados
  con filtro manual, chips de relevancia y promoción de actores → exportar; editor de
  sectores con selector geográfico; asistente para crear sectores con ayuda de IA externa
  (la app no llama a ningún modelo); identidad visual institucional.
- **Empaquetado:** PyInstaller (`.app` de macOS, `.exe` de Windows) e instaladores
  (`.dmg` e Inno Setup) compilados en GitHub Actions, que publica los instaladores y sus
  checksums al taggear una versión `vX.Y.Z`.

Para usarla, ver **[Instalar](#instalar)**. Para correr desde el código, ver
**[Desarrollo](#desarrollo)**.

## Desarrollo

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# pruebas
pytest

# uso por terminal (mismo motor que la GUI)
python -m compscrapper.cli --importar mi_sector.json
python -m compscrapper.cli --listar
python -m compscrapper.cli --sector "mi sector" --salida resultado.xlsx
```

> **Nota para desarrollar en macOS:** no uses el Python de CommandLineTools
> (`/usr/bin/python3`) para el venv — no configura bien los plugins de Qt y la app aborta
> con `Could not find the Qt platform plugin "cocoa" in ""`. Usá un Python de Homebrew
> (`brew install python@3.13`) y, preferiblemente, un venv fuera de carpetas sincronizadas
> por iCloud (iCloud marca archivos como ocultos y Qt omite los plugins ocultos). Si
> instalás PySide6 con el Python de sistema, agregá `--no-compile` para evitar un error al
> pre-compilar un archivo plantilla del paquete.

Los sectores se guardan como JSON en la carpeta de datos del sistema operativo
(`~/Library/Application Support/COMPScrapper/sectores` en Mac;
`%APPDATA%\COMPScrapper\sectores` en Windows). En el primer arranque se instala el sector
semilla **"Carne"** como ejemplo; es editable y borrable.

## Sin IA

El motor es determinista: RSS de Google News + expresiones regulares + heurísticas. No
depende de ningún modelo ni servicio de IA. De todos modos, ofrece la posibilidad de usar
una IA externa para asistir en la configuración de los parámetros del sector.

## Licencia

[MIT](LICENSE) © 2026 Carlos Centurión.

## Créditos

Desarrollada por Carlos Centurión. Parte del desarrollo se hizo con asistencia de
Claude (Anthropic); el diseño, las decisiones y la validación son del autor.
