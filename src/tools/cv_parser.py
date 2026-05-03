# ============================================================
# SECCIÓN 3: Extractor estructurado de CVs
# ============================================================
import uuid
from pathlib import Path

import fitz

from clients.client_llm import LLMClient
from logger import get_logger
from models.schemas import CVEstructurado
from tools.cv_anonymizer import CVAnonymizer

logger = get_logger(__name__)


class CVParser:
    """
    Clase encargada de orquestar el pipeline completo de procesamiento de
    Curriculums Vitae.

    Su función es transformar archivos físicos (PDF, DOCX) o texto bruto en objetos
    'CVEstructurado' validados. El proceso incluye la extracción de texto, la
    anonimización de datos sensibles mediante 'CVAnonymizer' y la extracción de
    información profesional utilizando un LLM.
    """

    def __init__(self):
        self.anonymizer = CVAnonymizer()
        self.cliente = LLMClient(
            modelo="gpt-4o-mini",  # Económico para procesamiento masivo
            temperatura=0.0,
            max_tokens=1200,
        )

    def _extraer_texto_pdf(self, ruta: Path) -> str:
        """
        Extrae el contenido textual de un archivo PDF utilizando PyMuPDF.

        Args:
            ruta (Path): Ruta al archivo PDF.

        Returns:
            str: Texto extraído de todas las páginas del documento.
        """
        doc = fitz.open(ruta)
        texto = "\n".join(pagina.get_text("text") for pagina in doc)
        doc.close()
        return texto

    def _extraer_texto_docx(self, ruta: Path) -> str:
        """
        Extrae el contenido textual de un archivo DOCX utilizando python-docx.

        Args:
            ruta (Path): Ruta al archivo DOCX.

        Returns:
            str: Texto extraído de los párrafos del documento.
        """
        try:
            from docx import Document

            doc = Document(ruta)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            logger.warning("python-docx no instalado. pip install python-docx")
            return ""

    def parsear_texto_cv(self, texto_crudo: str) -> CVEstructurado:
        """
        Procesa texto bruto de un CV para convertirlo en una estructura objetiva.

        Aplica anonimización para eliminar PII (Información de Identificación Personal)
        y luego utiliza el LLM para identificar experiencia, skills y educación.

        Args:
            texto_crudo (str): El texto original extraído del CV.

        Returns:
            CVEstructurado: Objeto con la información profesional extraída y validada.
        """
        # Paso 1: Anonimizar (Aplica lógica heurística para proteger la privacidad)
        texto_anonimizado = self.anonymizer.anonimizar_texto(texto_crudo)

        # Paso 2: Extraer estructura con LLM
        system_prompt = """Eres un analizador experto de CVs para el mercado laboral peruano.
Extrae información profesional del CV de forma objetiva y estructurada.
NUNCA incluyas nombre completo, DNI, teléfono, email ni dirección en tu respuesta.
Enfócate en competencias, experiencia y formación profesional."""

        user_message = f"""Analiza este CV y extrae la información estructurada:

{texto_anonimizado[:3000]}

El 'candidato_id' debe ser exactamente: "{uuid.uuid4()}"
"""
        cv_estructurado = self.cliente.llamar(
            system_prompt=system_prompt,
            user_message=user_message,
            schema=CVEstructurado,
        )

        logger.debug(
            "CV estructurado: %s",
            cv_estructurado.model_dump_json(indent=2, ensure_ascii=False),
        )

        return cv_estructurado

    def parsear_archivo_cv(self, ruta: Path) -> CVEstructurado:
        """
        Lee un archivo de CV y lo procesa a través del pipeline completo.

        Identifica el formato del archivo (PDF o DOCX), extrae el texto y llama
        al proceso de estructuración.

        Args:
            ruta (Path): Ubicación del archivo del CV.

        Returns:
            CVEstructurado: Resultado del procesamiento estructurado.
        """
        # Paso 1: Extraer texto según formato
        if ruta.suffix.lower() == ".pdf":
            texto_crudo = self._extraer_texto_pdf(ruta)
        elif ruta.suffix.lower() in [".docx", ".doc"]:
            texto_crudo = self._extraer_texto_docx(ruta)
        else:
            # Si es texto plano o formato desconocido, intentamos leer como texto
            try:
                texto_crudo = ruta.read_text(encoding="utf-8")
            except Exception:
                raise ValueError(f"Formato no soportado o error al leer: {ruta.suffix}")

        return self.parsear_texto_cv(texto_crudo)

    def parsear_cv(self, ruta: Path) -> CVEstructurado:
        """
        Metodo legacy para mantener compatibilidad con versiones anteriores.
        Delega la funcionalidad a parsear_archivo_cv.
        """
        return self.parsear_archivo_cv(ruta)
