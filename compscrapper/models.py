"""Estructuras de datos del dominio.

Se mantienen como dataclasses planas, serializables a/desde JSON, para que la
configuración de sectores sea *datos* (no código) y para que la interfaz y el
motor compartan tipos sin acoplarse entre sí.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Sector:
    """Definición de un sector/mercado a monitorear.

    Las tres dimensiones de términos se usan para puntuar la relevancia de cada
    titular: un artículo relevante toca al menos dos de las tres.
      - terminos_sector:   identifican el mercado y sus actores.
      - terminos_queja:    tono de problema de competencia.
      - terminos_contexto: ámbito o contexto específico (compras públicas,
        regulación, fusión, importación...). Genérico: no presupone licitaciones.

    `ambito_geografico` acota la búsqueda a nivel subnacional (lista de lugares;
    vacío = nacional). `exclusiones` son términos de ruido propios del sector que
    el descubrimiento de actores debe ignorar (además del ruido genérico).
    """

    nombre: str
    descripcion: str = ""
    terminos_sector: list[str] = field(default_factory=list)
    terminos_queja: list[str] = field(default_factory=list)
    terminos_contexto: list[str] = field(default_factory=list)
    consultas: list[str] = field(default_factory=list)
    consultas_descubrimiento: list[str] = field(default_factory=list)
    ambito_geografico: list[str] = field(default_factory=list)
    exclusiones: list[str] = field(default_factory=list)
    # Dominios de fuentes propias del sector (p. ej. gremios/cámaras del rubro:
    # 'arp.org.py', 'capasu.org.py'). Se suman como OR a la búsqueda SOLO de este
    # sector, además del ancla de país. Se guardan sin el prefijo 'site:'.
    dominios_fuente: list[str] = field(default_factory=list)

    def dimensiones(self) -> dict[str, list[str]]:
        return {
            "terminos_sector": self.terminos_sector,
            "terminos_queja": self.terminos_queja,
            "terminos_contexto": self.terminos_contexto,
        }

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Sector":
        """Construye un Sector validando tipos. No ejecuta nada del JSON."""
        if not isinstance(data, dict):
            raise ValueError("La configuración del sector debe ser un objeto JSON.")
        if not isinstance(data.get("nombre"), str) or not data["nombre"].strip():
            raise ValueError("El sector necesita un 'nombre' de texto no vacío.")

        def lista_de_texto(valor, campo, dividir_comas=False) -> list[str]:
            if valor is None:
                return []
            if not isinstance(valor, list) or not all(isinstance(x, str) for x in valor):
                raise ValueError(f"El campo '{campo}' debe ser una lista de textos.")
            # Convención uniforme: los valores se separan por coma (y por salto de
            # línea). Sin esto, "a, b, c" se tomaría como un único término/consulta
            # y no matchearía nunca.
            items = []
            for x in valor:
                partes = x.split(",") if dividir_comas else [x]
                items.extend(p.strip() for p in partes if p.strip())
            return items

        descripcion = data.get("descripcion", "")
        if not isinstance(descripcion, str):
            raise ValueError("El campo 'descripcion' debe ser texto.")

        # 'terminos_compras' se acepta como nombre heredado de 'terminos_contexto'.
        contexto = data.get("terminos_contexto", data.get("terminos_compras"))

        return cls(
            nombre=data["nombre"].strip(),
            descripcion=descripcion.strip(),
            terminos_sector=lista_de_texto(data.get("terminos_sector"), "terminos_sector", True),
            terminos_queja=lista_de_texto(data.get("terminos_queja"), "terminos_queja", True),
            terminos_contexto=lista_de_texto(contexto, "terminos_contexto", True),
            consultas=lista_de_texto(data.get("consultas"), "consultas", True),
            consultas_descubrimiento=lista_de_texto(
                data.get("consultas_descubrimiento"), "consultas_descubrimiento", True
            ),
            ambito_geografico=lista_de_texto(data.get("ambito_geografico"), "ambito_geografico", True),
            exclusiones=lista_de_texto(data.get("exclusiones"), "exclusiones", True),
            dominios_fuente=lista_de_texto(data.get("dominios_fuente"), "dominios_fuente", True),
        )


@dataclass
class Noticia:
    """Una noticia encontrada. `mantener` lo controla el filtro manual."""

    relevancia: int
    titulo: str
    fuente: str
    terminos: list[str]
    fecha_publicacion: Optional[datetime]
    url: str
    url_resaltado: str
    consulta: str
    mantener: bool = True


@dataclass
class ActorCandidato:
    """Organización candidata detectada en los cuerpos de las notas."""

    candidato: str
    menciones: int
    titular_ejemplo: str
    mantener: bool = True  # lo controla el filtro manual antes de exportar


@dataclass
class Progreso:
    """Reporte de avance que el motor emite por callback hacia la interfaz."""

    fase: str  # 'monitoreo' | 'resolucion' | 'descubrimiento'
    actual: int
    total: int
    mensaje: str
