"""Textos de ayuda y ejemplos para los campos del editor de sector.

Centralizados acá para mantener un tono uniforme y poder ajustarlos sin tocar
la lógica de la interfaz.
"""

NOMBRE = "Nombre corto del mercado o tema. Ej.: Carne, Combustibles, Telefonía móvil."

DESCRIPCION = (
    "Una línea que resume qué se busca. "
    "Ej.: Sospechas de coordinación de precios y concentración en la industria frigorífica."
)

TERMINOS_SECTOR = (
    "Palabras que identifican el mercado y sus actores, separadas por coma. El motor "
    "las usa para reconocer de qué mercado habla una noticia.\n"
    "Ej.: frigorífico, carne, ganado, ganadero, faena"
)

TERMINOS_QUEJA = (
    "Palabras que señalan un problema de competencia, separadas por coma.\n"
    "Ej.: denuncia, reclamo, competencia desleal, monopolio, barreras, exclusión"
)

TERMINOS_CONTEXTO = (
    "Palabras del ámbito o contexto específico de interés, separadas por coma. No "
    "tiene que ser compras públicas: puede ser regulación, fusión, importación, etc.\n"
    "Ej.: licitación, adjudicación, DNCP, regulación, importación"
)

CONSULTAS = (
    "Consultas de búsqueda, separadas por coma. Cada una se envía a Google News. "
    "Conviene que expresen la intención completa; se admiten comillas y OR.\n"
    'Ej.: frigoríficos Conacom, ganaderos denuncian competencia desleal'
)

CONSULTAS_DESCUBRIMIENTO = (
    "Consultas genéricas para descubrir actores del mercado, separadas por coma. De "
    "los cuerpos de esas notas se extraen nombres de empresas y gremios candidatos.\n"
    "Ej.: principales frigoríficos Paraguay, gremios ganaderos Paraguay"
)

EXCLUSIONES = (
    "Palabras de ruido propias de este mercado que el descubrimiento de actores debe "
    "ignorar, separadas por coma. El ruido genérico del español ya está contemplado.\n"
    "Ej.: feria, vacunación"
)

DOMINIOS_FUENTE = (
    "Sitios propios del sector (solo el dominio), separados por coma: gremios, cámaras "
    "o portales del rubro. Sus notas entran aunque no nombren al país. Sirve para "
    "rubros con fuentes especializadas; dejalo vacío si no hace falta.\n"
    "Gremios indexados en Google News (elegí los de tu rubro): "
    "uip.org.py (industria), ugp.org.py (producción), capeco.org.py (exportadores), "
    "arp.org.py (ganadería), capadei.org.py (tecnología), capaco.org.py (construcción), "
    "cifarma.org.py (farmacéutica), apcs.org.py (seguros), capasu.org.py (supermercados), "
    "cip.org.py (importadores), ccparaguay.com.py (comercio)"
)

AMBITO_GEOGRAFICO = (
    "Acota la búsqueda geográficamente. Nacional cubre todo el país. También podés "
    "elegir uno o varios departamentos completos, o ciudades puntuales."
)

DESCUBRIR = (
    "Además de las noticias, intenta descubrir empresas y gremios del mercado a partir "
    "de los cuerpos de las notas. Hace la búsqueda más lenta."
)

RANGO_FECHAS = (
    "Limita las noticias a un período. Si se desactiva, se toman las más recientes "
    "que devuelva el buscador."
)
