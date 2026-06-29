"""Motor de monitoreo de noticias: búsqueda, puntuación y descubrimiento de actores.

Sin interfaz. Se comunica con la GUI por dos callbacks opcionales:
  - on_progress(Progreso): para la barra de progreso.
  - should_cancel() -> bool: se consulta entre pedidos; si devuelve True, corta
    limpio levantando BusquedaCancelada.

Las funciones puras (strip_accents, score_relevance, highlight_url, extracción
de actores) son deterministas y están cubiertas por pruebas.
"""

from __future__ import annotations

import logging
import re
import time
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from email.utils import parsedate_to_datetime
from typing import Callable, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from googlenewsdecoder import gnewsdecoder

from .models import ActorCandidato, Noticia, Progreso, Sector

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=es&gl=PY&ceid=PY:es"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "es-PY,es;q=0.9",
}

ProgressCb = Optional[Callable[[Progreso], None]]
CancelCb = Optional[Callable[[], bool]]


class BusquedaCancelada(Exception):
    """Se levanta cuando should_cancel() devuelve True."""


# ---------------------------------------------------------------------------
# Funciones puras (deterministas, sin red)
# ---------------------------------------------------------------------------
def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


# Terminaciones de género/número que se consideran la misma palabra. El objetivo
# es temático: "frigorífico"/"frigoríficos", "lácteo"/"láctea"/"lácteos"/"lácteas"
# valen igual. Se limita a flexión de sustantivos/adjetivos (no conjugación
# verbal) y a un conjunto cerrado de sufijos para no caer en derivaciones falsas
# (p. ej. "precio" NO debe matchear "precioso").
_FLEXION = "(?:o|a|e|os|as|es|s)?"


def _palabra_regex(w: str) -> str:
    """Regex de una palabra (ya normalizada) tolerante a género/número.

    Toma la raíz quitando el plural y la vocal de género final, y vuelve a
    admitir esas terminaciones. Palabras cortas o no alfabéticas van literales.
    """
    if len(w) < 4 or not w.isalpha():
        return re.escape(w)
    raiz = w
    if raiz.endswith("es") and len(raiz) - 2 >= 3:
        raiz = raiz[:-2]
    elif raiz.endswith("s") and len(raiz) - 1 >= 3:
        raiz = raiz[:-1]
    if raiz and raiz[-1] in "oa" and len(raiz) - 1 >= 3:
        raiz = raiz[:-1]
    return re.escape(raiz) + _FLEXION


def termino_regex(termino_norm: str) -> str:
    """Patrón para un término (posiblemente multipalabra), ya normalizado, que
    matchea sus variantes de género/número con límites de palabra."""
    cuerpo = r"\s+".join(_palabra_regex(w) for w in termino_norm.split())
    return r"\b" + cuerpo + r"\b"


def score_relevance(text: str, sector: Sector) -> tuple[int, list[str]]:
    """(nivel de relevancia, términos hallados). Palabra completa, insensible a
    acentos.

    La dimensión SECTOR es obligatoria: si la nota no menciona el mercado, no es
    relevante por más que hable de "acuerdos" o "precios" en general. Dado que
    toca el sector, el nivel ordena por qué más toca:
      - 3: sector + queja/competencia + contexto.
      - 2: sector + queja/competencia.
      - 1: sector + contexto (sin queja).
      - 0: no toca el sector, o lo toca solo a él (el motor la descarta).
    """
    normalized = strip_accents(text.lower())
    dims_hit: set[str] = set()
    terms: list[str] = []
    for clave, terminos in sector.dimensiones().items():
        hits = [
            t
            for t in terminos
            if re.search(termino_regex(strip_accents(t.lower())), normalized)
        ]
        if hits:
            dims_hit.add(clave)
            terms.extend(hits)
    if "terminos_sector" not in dims_hit:
        return 0, terms
    tiene_queja = "terminos_queja" in dims_hit
    tiene_contexto = "terminos_contexto" in dims_hit
    if tiene_queja and tiene_contexto:
        nivel = 3
    elif tiene_queja:
        nivel = 2
    elif tiene_contexto:
        nivel = 1
    else:
        nivel = 0  # solo sector: una dimensión, insuficiente
    return nivel, terms


def highlight_url(direct_url: str, title: str, terms: list[str], max_fragments: int = 4) -> str:
    """URL con text fragments (#:~:text=) que resaltan los términos al abrir la página."""
    normalized = strip_accents(title.lower())
    spans = []
    for term in terms:
        m = re.search(termino_regex(strip_accents(term.lower())), normalized)
        if m:
            spans.append(title[m.start():m.end()])  # mismo largo: NFD 1:1
    fragments = []
    for span in dict.fromkeys(spans):  # únicos, preservando orden
        fragments.append(quote(span, safe=""))
        if len(fragments) >= max_fragments:
            break
    if not fragments:
        return ""
    return direct_url + "#:~:text=" + "&text=".join(fragments)


# ---------------------------------------------------------------------------
# Expansión geográfica (subnacional)
# ---------------------------------------------------------------------------
MAX_GEO_OR = 12  # términos de lugar por consulta antes de dividir en lotes

# Ancla de país para el ámbito "Nacional". La edición de Google News (gl=PY) NO
# restringe los resultados a medios paraguayos: solo fija idioma y ranking, así
# que sin esto entran notas de otros países. Se inyecta como un único grupo OR
# en cada consulta nacional.
#
# Dos anclas complementarias:
#   - términos-país: atrapan notas (incluso de medios extranjeros o sin dominio
#     propio) que nombran a Paraguay;
#   - dominios de medios paraguayos (operador site:): atrapan las notas
#     NACIONALES, que casi nunca nombran al país por ser de consumo interno.
# Dominios verificados en vivo contra Google News (los que devuelven resultados).
PAIS_TERMINOS = ["Paraguay", "paraguayo", "paraguaya"]
# Dominios de medios paraguayos (operador site:), agrupados por categoría para
# facilitar la edición. La herramienta es multisectorial, así que la lista
# busca cobertura general del país, no de un rubro. Todos verificados en vivo
# contra Google News. Para agregar/quitar, mantené el prefijo "site:".
_MEDIOS_GENERALES = [
    "site:abc.com.py",        # ABC Color
    "site:ultimahora.com",    # Última Hora
    "site:lanacion.com.py",   # La Nación
    "site:hoy.com.py",        # Diario HOY
    "site:elnacional.com.py", # El Nacional
    "site:npy.com.py",        # Nación Media / NPY
    "site:gen.com.py",        # GEN
    "site:paraguay.com",      # Paraguay.com
    "site:adndigital.com.py", # ADN Digital
    "site:extra.com.py",      # Extra
    "site:cronica.com.py",    # Crónica
    "site:ahora.com.py",      # Ahora
]
_MEDIOS_ECONOMICOS = [
    "site:5dias.com.py",      # 5 Días
    "site:marketdata.com.py", # MarketData
    "site:infonegocios.com.py",  # InfoNegocios
]
_MEDIOS_RADIO_TV = [
    "site:unicanal.com.py",   # Unicanal
    "site:c9n.com.py",        # C9N
    "site:telefuturo.com.py", # Telefuturo
    "site:trece.com.py",      # Trece
    "site:nanduti.com.py",    # Radio Ñandutí
    "site:monumental.com.py", # 780 AM La Monumental
    "site:launion.com.py",    # La Unión 800 AM
]
_MEDIOS_INSTITUCIONALES = [
    "site:ip.gov.py",         # Agencia IP (prensa estatal)
    "site:bcp.gov.py",        # Banco Central del Paraguay
    "site:set.gov.py",        # Subsecretaría de Tributación (SET)
]
MEDIOS_PY = (
    _MEDIOS_GENERALES + _MEDIOS_ECONOMICOS
    + _MEDIOS_RADIO_TV + _MEDIOS_INSTITUCIONALES
)
GEO_NACIONAL = PAIS_TERMINOS + MEDIOS_PY


def _quote_term(term: str) -> str:
    return f'"{term}"' if " " in term else term


def geo_batches(terms: list[str], max_or: int = MAX_GEO_OR):
    """Divide los términos de lugar en lotes manejables. Lista vacía -> [None]
    (sin restricción geográfica: ámbito nacional)."""
    if not terms:
        return [None]
    return [terms[i:i + max_or] for i in range(0, len(terms), max_or)]


def apply_geo(query: str, batch) -> str:
    """Agrega a la consulta un grupo OR de lugares; los multipalabra van entre comillas."""
    if not batch:
        return query
    grupo = " OR ".join(_quote_term(t) for t in batch)
    return f"{query} ({grupo})"


def date_clause(desde=None, hasta=None) -> str:
    """Operadores de fecha de Google News: 'after:YYYY-MM-DD before:YYYY-MM-DD'.
    Acepta date/datetime o None. Devuelve cadena vacía si no hay fechas."""
    partes = []
    if desde is not None:
        partes.append(f"after:{desde.strftime('%Y-%m-%d')}")
    if hasta is not None:
        partes.append(f"before:{hasta.strftime('%Y-%m-%d')}")
    return " ".join(partes)


def _como_site(dominios) -> list[str]:
    """Normaliza dominios del sector al operador site: (idempotente)."""
    out = []
    for d in dominios or []:
        d = d.strip()
        if d:
            out.append(d if d.startswith("site:") else f"site:{d}")
    return out


def expand_queries(consultas, ambito_geografico, max_or: int = MAX_GEO_OR,
                   desde=None, hasta=None, dominios_sector=None) -> list[str]:
    """Consultas efectivas: cada consulta base por cada lote geográfico, con el
    rango de fechas aplicado.

    - Nacional (sin ámbito): se ancla cada consulta al grupo país completo
      (términos + dominios de medios) en un único grupo OR, sin lotear, para que
      siga siendo una sola consulta por base.
    - Subnacional: las localidades elegidas se inyectan loteadas (con muchas
      ciudades se divide en grupos y la deduplicación por título une los
      resultados).

    `dominios_sector` son fuentes propias del sector (gremios/cámaras del rubro);
    se suman como OR a cada grupo, así una nota de esa fuente entra aunque no
    nombre al país ni la localidad.
    """
    extras = _como_site(dominios_sector)
    if ambito_geografico:
        batches = geo_batches(ambito_geografico, max_or)
        batches = [b + extras for b in batches]
    else:
        batches = [GEO_NACIONAL + extras]  # ancla nacional, un solo grupo sin lotear
    fechas = date_clause(desde, hasta)
    consultas_efectivas = [apply_geo(q, b) for q in consultas for b in batches]
    if fechas:
        consultas_efectivas = [f"{q} {fechas}" for q in consultas_efectivas]
    return consultas_efectivas


# Ruido genérico del español de noticias. El ruido específico de un sector
# (palabras propias del rubro que no son actores) va en Sector.exclusiones, no
# aquí, para que el descubrimiento de actores sea genérico entre mercados.
_STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "de", "del", "y", "en", "con",
    "por", "para", "sobre", "tras", "ante", "hasta", "desde", "paraguay",
    "asuncion", "gobierno", "estado", "ministerio", "video", "foto", "hoy",
    "segun", "asi", "este", "esta", "estos", "estas", "nuevo", "nueva",
    "usd", "millones", "guaranies", "dia", "suba",
    "produccion", "exportaciones", "importaciones", "desafios",
    "inauguran", "buscan", "sector", "industria", "mercado", "precio",
}
_CONNECTORS = {"de", "del", "la", "las", "los", "y", "el"}

# Palabras comunes que aparecen en MAYÚSCULAS en titulares y que el patrón de
# siglas sueltas confundía con actores (p. ej. "CÓMO", "AFECTARÍA"). Las siglas
# reales (INC, DNCP, CONACOM, INTN, ANDE) no llevan acento ni son palabras del
# idioma, así que se filtran por acento + esta lista.
_PALABRAS_COMUNES = {
    # conectores / adverbios / pronombres
    "como", "para", "esto", "esta", "este", "esos", "esas", "desde", "hasta",
    "donde", "cuando", "porque", "segun", "aunque", "mientras", "sobre", "entre",
    "ante", "tras", "tambien", "ademas", "ahora", "luego", "antes", "nunca",
    "siempre", "todos", "todas", "mucho", "muchos", "menos", "solo", "incluso",
    "contra", "durante", "mediante", "asimismo",
    # verbos frecuentes en titulares (infinitivos y conjugaciones)
    "afectaria", "autorizo", "seria", "habria", "estaria", "entrar", "salir",
    "llegar", "pasar", "hacer", "decir", "lograr", "evitar", "frenar", "exigir",
    "pedir", "lanzar", "abrir", "cerrar", "subir", "bajar", "ganar", "perder",
    "denuncio", "denuncian", "afirma", "afirman", "asegura", "aseguran",
    "confirma", "niega", "niegan", "pide", "piden", "exige", "exigen", "reclama",
    "rechaza", "apoya", "advierte", "anuncia", "anuncian", "alerta", "preocupa",
    # sustantivos / adjetivos de titular y pies de foto
    "gentileza", "archivo", "ilustracion", "imagen", "lista", "salida", "entrada",
    "aviso", "atencion", "urgente", "video", "nota", "dato", "datos", "caso",
    "tema", "parte", "gente", "vida", "pais", "ciudad", "total", "final", "gran",
    "ultimo", "ultima", "nuevo", "nueva", "gratis", "oferta", "peligro", "cuidado",
    "ojo", "mira", "entrevista", "opinion", "editorial", "resumen", "informe",
}

_KNOWN_ACRONYMS = {
    "dncp", "mec", "mag", "mic", "mds", "ips", "usd", "covid", "abc", "efe",
    "onu", "fao", "bid", "pib", "iva", "ande", "essap", "senave", "senacsa",
    "conacom", "mipymes", "pymes", "ltda", "unesco", "unicef", "oms", "ops",
    "union europea", "mercosur", "banco mundial", "banco central",
}

_ORG_PATTERNS = [
    re.compile(
        r"\b((?:Cooperativa|Cámara|Camara|Asociación|Asociacion|Federación|"
        r"Federacion|Consorcio|Sindicato|Unión|Union|Gremio|Central|Frente)"
        r"(?:\s+(?:de|del|de\s+la|de\s+los|la|las|los|y)\b|"
        r"\s+[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+){1,6})"
    ),
    re.compile(
        r"\b((?:[A-ZÁÉÍÓÚÑ][\wáéíóúñ&.]*\s+){1,4}"
        r"S\.?\s?A\.?(?:E\.?C\.?A\.?)?)(?=[\s,.;:)]|$)"
    ),
    re.compile(r"\b([A-ZÁÉÍÓÚÑ]{4,12})\b"),
]

# Tokens alfabéticos (≥2 letras) para detectar si una palabra aparece en
# minúscula/capitalizada en el corpus (ver no_mayus en extract_actor_candidates).
_PALABRA_RE = re.compile(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{2,}")


def _clean_candidate(candidate: str) -> str:
    words = candidate.strip(" .,;:").split()
    while words and strip_accents(words[-1].lower()) in _CONNECTORS:
        words.pop()
    return " ".join(words)


def extract_actor_candidates(texts, known_actors, exclusiones=None) -> list[ActorCandidato]:
    """Extrae organizaciones candidatas (gremios, cámaras, cooperativas, empresas
    S.A., siglas) de textos de noticias. Heurística para revisión humana.

    `exclusiones` es el ruido específico del sector (además del genérico): términos
    que no deben tomarse como actores candidatos.
    """
    known = {strip_accents(a.lower()) for a in known_actors}
    extra = {strip_accents(e.lower()) for e in (exclusiones or [])}
    stop = _STOPWORDS | _CONNECTORS | extra

    # Palabras que en el corpus aparecen alguna vez NO en mayúsculas (minúscula o
    # capitalizadas). Una sigla real (DNCP, INTN) nunca aparece así; una palabra
    # común que quedó en mayúsculas en un titular, sí. Es la prueba determinista
    # de "¿esto es una sigla o solo una palabra gritada?" — sin analizador morfológico.
    no_mayus = set()
    for text, _ in texts:
        for tok in _PALABRA_RE.findall(text):
            if not tok.isupper():
                no_mayus.add(strip_accents(tok.lower()))

    counter: Counter = Counter()
    samples: dict[str, str] = {}
    for text, source_label in texts:
        found_here = set()
        for pattern in _ORG_PATTERNS:
            for match in pattern.finditer(text):
                candidate = _clean_candidate(match.group(1))
                norm = strip_accents(candidate.lower())
                norm_words = norm.split()
                # Sigla suelta (un solo token en mayúsculas): solo vale como actor
                # si no lleva acento, no es palabra común y NO aparece en minúscula
                # en ninguna parte del corpus (una palabra del idioma sí aparecería).
                sigla_suelta = " " not in candidate and candidate.isupper()
                if sigla_suelta and (
                    any(c in "ÁÉÍÓÚÜ" for c in candidate)
                    or norm in _PALABRAS_COMUNES
                    or norm in no_mayus
                ):
                    continue
                if (
                    not candidate
                    or norm in known
                    or norm in extra
                    or any(norm == k or norm in k or k in norm for k in known)
                    or norm in _KNOWN_ACRONYMS
                    or all(w in stop for w in norm_words)
                ):
                    continue
                found_here.add(candidate)
        for candidate in found_here:
            counter[candidate] += 1
            samples.setdefault(candidate, source_label)
    return [
        ActorCandidato(candidato=name, menciones=count, titular_ejemplo=samples[name])
        for name, count in counter.most_common(40)
        if count >= 2
    ]


# ---------------------------------------------------------------------------
# Motor (red)
# ---------------------------------------------------------------------------
class NewsEngine:
    def __init__(
        self,
        timeout: int = 15,
        sleep: float = 1.5,
        max_items: int = 40,
        max_discovery_pages: int = 25,
        session: Optional[requests.Session] = None,
    ):
        self.timeout = timeout
        self.sleep = sleep
        self.max_items = max_items
        self.max_discovery_pages = max_discovery_pages
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)

    # -- utilidades internas --
    def _check_cancel(self, should_cancel: CancelCb) -> None:
        if should_cancel and should_cancel():
            raise BusquedaCancelada()

    def _emit(self, on_progress: ProgressCb, fase, actual, total, mensaje) -> None:
        if on_progress:
            on_progress(Progreso(fase=fase, actual=actual, total=total, mensaje=mensaje))

    def _fetch_rss_items(self, query: str) -> list[dict]:
        url = GOOGLE_NEWS_RSS.format(query=quote(query))
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = []
        for item in list(root.iter("item"))[: self.max_items]:
            try:
                pub_date = parsedate_to_datetime(item.findtext("pubDate"))
            except (TypeError, ValueError):
                pub_date = None
            items.append(
                {
                    "title": (item.findtext("title") or "").strip(),
                    "link": (item.findtext("link") or "").strip(),
                    "source": (item.findtext("source") or "").strip(),
                    "pub_date": pub_date,
                }
            )
        return items

    def _resolve_direct_url(self, google_news_link: str) -> str:
        try:
            result = gnewsdecoder(google_news_link, interval=1)
            if result.get("status") and result.get("decoded_url"):
                return result["decoded_url"]
            logger.warning("No se pudo decodificar: %s", result.get("message", "?"))
        except Exception as e:  # noqa: BLE001 - red externa, no debe abortar la corrida
            logger.warning("Error decodificando URL: %s", e)
        return google_news_link

    def _fetch_article_text(self, url: str, max_chars: int = 20000) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        return " ".join(paragraphs)[:max_chars]

    # -- API pública --
    def buscar(
        self,
        sector: Sector,
        descubrir: bool = True,
        desde=None,
        hasta=None,
        on_progress: ProgressCb = None,
        should_cancel: CancelCb = None,
    ) -> tuple[list[Noticia], list[ActorCandidato]]:
        noticias = self._monitorear(sector, desde, hasta, on_progress, should_cancel)
        actores: list[ActorCandidato] = []
        if descubrir:
            actores = self._descubrir(sector, noticias, desde, hasta, on_progress, should_cancel)
        return noticias, actores

    def _monitorear(self, sector, desde, hasta, on_progress, should_cancel) -> list[Noticia]:
        crudas = []
        consultas = expand_queries(sector.consultas, sector.ambito_geografico,
                                   desde=desde, hasta=hasta,
                                   dominios_sector=sector.dominios_fuente)
        total = len(consultas)
        for i, query in enumerate(consultas, 1):
            self._check_cancel(should_cancel)
            self._emit(on_progress, "monitoreo", i, total, f"Consulta: {query}")
            try:
                for item in self._fetch_rss_items(query):
                    score, terms = score_relevance(item["title"], sector)
                    if score < 1:  # nivel 0 = menos de 2 dimensiones tocadas
                        continue
                    crudas.append(
                        {
                            "relevancia": score,
                            "titulo": item["title"],
                            "fuente": item["source"] or "Google News",
                            "terminos": terms,
                            "fecha_publicacion": item["pub_date"],
                            "url": item["link"],
                            "consulta": query,
                        }
                    )
            except Exception as e:  # noqa: BLE001
                logger.error("Error en consulta '%s': %s", query, e)
            time.sleep(self.sleep)

        # Deduplicar por título normalizado, conservando el mejor puntaje.
        seen: dict[str, dict] = {}
        for art in crudas:
            key = strip_accents(art["titulo"].lower())
            if key not in seen or art["relevancia"] > seen[key]["relevancia"]:
                seen[key] = art
        unique = list(seen.values())
        unique.sort(
            key=lambda a: (
                -a["relevancia"],
                -(a["fecha_publicacion"].timestamp() if a["fecha_publicacion"] else 0),
            )
        )

        # Resolver URLs directas solo para las que quedaron.
        total = len(unique)
        noticias = []
        for i, art in enumerate(unique, 1):
            self._check_cancel(should_cancel)
            self._emit(on_progress, "resolucion", i, total, "Resolviendo enlaces directos...")
            direct = self._resolve_direct_url(art["url"])
            noticias.append(
                Noticia(
                    relevancia=art["relevancia"],
                    titulo=art["titulo"],
                    fuente=art["fuente"],
                    terminos=art["terminos"],
                    fecha_publicacion=art["fecha_publicacion"],
                    url=direct,
                    url_resaltado=highlight_url(direct, art["titulo"], art["terminos"]),
                    consulta=art["consulta"],
                )
            )
        return noticias

    def _descubrir(self, sector, noticias, desde, hasta, on_progress, should_cancel) -> list[ActorCandidato]:
        texts: list[tuple[str, str]] = []
        page_urls: list[tuple[str, str]] = []

        consultas_desc = expand_queries(sector.consultas_descubrimiento, sector.ambito_geografico,
                                        desde=desde, hasta=hasta,
                                        dominios_sector=sector.dominios_fuente)
        total = len(consultas_desc)
        for i, query in enumerate(consultas_desc, 1):
            self._check_cancel(should_cancel)
            self._emit(on_progress, "descubrimiento", i, total, f"Descubrimiento: {query}")
            try:
                for item in self._fetch_rss_items(query):
                    texts.append((item["title"], item["title"]))
                    page_urls.append((item["link"], item["title"]))
            except Exception as e:  # noqa: BLE001
                logger.error("Error en descubrimiento '%s': %s", query, e)
            time.sleep(self.sleep)

        # Minar primero los cuerpos de las noticias relevantes (URL ya resuelta).
        direct_first = [
            (n.url, n.titulo)
            for n in noticias
            if not n.url.startswith("https://news.google.com")
        ]
        seen_urls = set()
        fetched = 0
        for url, title in direct_first + page_urls:
            if fetched >= self.max_discovery_pages:
                break
            self._check_cancel(should_cancel)
            if url.startswith("https://news.google.com"):
                url = self._resolve_direct_url(url)
                if url.startswith("https://news.google.com"):
                    continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            try:
                body = self._fetch_article_text(url)
                if body:
                    texts.append((body, title))
                    fetched += 1
                    self._emit(
                        on_progress, "descubrimiento", fetched, self.max_discovery_pages,
                        "Analizando cuerpos de notas...",
                    )
            except Exception as e:  # noqa: BLE001
                logger.warning("No se pudo leer la nota (%s...): %s", title[:40], e)
            time.sleep(1)

        known = sector.terminos_sector + sector.terminos_contexto + sector.terminos_queja
        return extract_actor_candidates(texts, known, exclusiones=sector.exclusiones)
