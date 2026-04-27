from typing import Optional

from pathlib import Path
import fitz

from models.schemas import JobDescription
from clients.client_llm import LLMClient
from dotenv import load_dotenv
import logging
import uuid
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("cv-matcher.parser")
# ============================================================
# SECCIÓN 4: Parser de Job Descriptions
# ============================================================

class JDParser:
    """
    Clase encargada de extraer y estructurar información de descripciones de puesto (Job Descriptions).

    Su función es transformar textos de ofertas laborales (a menudo desestructurados)
    en objetos 'JobDescription' validados, extrayendo requisitos técnicos, años de
    experiencia y niveles de seniority para facilitar el matching con candidatos.
    """

    def __init__(self):
        self.cliente = LLMClient(
            modelo="gpt-4o-mini",
            temperatura=0.0,
            max_tokens=800,
        )

    def _extraer_texto_pdf(self, ruta: Path) -> str:
        """Extrae texto de una JD en PDF."""
        doc = fitz.open(ruta)
        texto = "\n".join(pagina.get_text("text") for pagina in doc)
        doc.close()
        return texto

    def _extraer_texto_docx(self, ruta: Path) -> str:
        """Extrae texto de una JD en DOCX."""
        try:
            from docx import Document
            doc = Document(ruta)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            logger.warning("python-docx no instalado. pip install python-docx")
            return ""

    def parsear_jd(self, texto_jd: str, titulo: str = "Puesto sin título") -> JobDescription:
        """
        Analiza el contenido de una JD y lo convierte en un objeto estructurado.

        Utiliza el parámetro 'titulo' proporcionado como contexto adicional para el LLM
        en caso de que el texto de la JD sea ambiguo sobre el cargo.

        Args:
            texto_jd (str): El contenido textual de la oferta laboral.
            titulo (str): Título sugerido o conocido del puesto.

        Returns:
            JobDescription: Instancia de Pydantic con los datos extraídos y validados.
        """
        system_prompt = """Eres un analizador experto de ofertas de empleo del mercado peruano.
Extrae los requisitos del puesto de forma clara y estructurada.
Distingue entre skills obligatorios (must-have) y deseables (nice-to-have)."""

        user_message = f"""Analiza esta Job Description y extrae la información estructurada.
Usa el siguiente título como referencia si es necesario: "{titulo}"

Contenido de la JD:
{texto_jd[:4000]}

El 'jd_id' debe ser exactamente: "{uuid.uuid4()}"
"""
        jd_estructurada = self.cliente.llamar(
            system_prompt=system_prompt,
            user_message=user_message,
            schema=JobDescription,
        )

        logger.info(f"JD_ESTRUCTURADA (Data): {jd_estructurada.model_dump()}")
        logger.info(f"JD_ESTRUCTURADA (Metadatos): {jd_estructurada.__class__.model_fields}")
        logger.info(f"JD_ESTRUCTURADA Métodos disponibles: {dir(jd_estructurada)}")

        # Si el LLM no extrajo un título o es muy genérico, usamos el título proporcionado
        if not jd_estructurada.titulo_puesto or jd_estructurada.titulo_puesto == "Puesto sin título":
            jd_estructurada.titulo_puesto = titulo

        return jd_estructurada

    def parsear_archivo_jd(self, ruta: Path, titulo: Optional[str] = None) -> JobDescription:
        """
        Lee un archivo (PDF/DOCX/TXT) y lo procesa como una Job Description.

        Args:
            ruta (Path): Ubicación del archivo de la JD.
            titulo (Optional[str]): Título opcional para ayudar al parser.

        Returns:
            JobDescription: El resultado del procesamiento estructurado.
        """
        if not titulo:
            titulo = ruta.stem.replace("-", " ").replace("_", " ").title()

        if ruta.suffix.lower() == ".pdf":
            texto_jd = self._extraer_texto_pdf(ruta)
        elif ruta.suffix.lower() in [".docx", ".doc"]:
            texto_jd = self._extraer_texto_docx(ruta)
        else:
            texto_jd = ruta.read_text(encoding="utf-8")

        return self.parsear_jd(texto_jd, titulo)