# """
# LAB01-03 — Cliente API y Parser de CVs para CV Matcher
#
# Módulo: 01 - Fundamentos e Ingeniería de IA
# Proyecto: CV Matcher
# Dependencias: LAB01-01 (reutiliza LLMClient)
# Entregable: proyectos/cv-matcher/src/tools/cv_parser.py
#              proyectos/cv-matcher/src/models/schemas.py
#
# Objetivo:
#     Construir el pipeline de extracción de información de CVs:
#     1. Parsear CVs en PDF y DOCX a texto limpio
#     2. Extraer campos estructurados con LLM (skills, experiencia, educación)
#     3. Anonimizar datos personales (nombre, DNI, teléfono, dirección)
#     4. Preparar los CVs para indexar en Qdrant (Módulo 02)
#     5. Parsear Job Descriptions (JDs) y extraer competencias requeridas
#
# Instrucciones:
#     1. Coloca un CV en PDF o DOCX en data/cvs_anonimizados/
#     2. Ejecuta: python LAB01-03-cliente-api-cvmatcher.py
#     3. Revisa el JSON generado con el CV anonimizado y estructurado
# """
#
# # ============================================================
# # SECCIÓN 0: Imports y configuración
# # ============================================================
#
# import re
# import uuid
# import logging
# import json
# from typing import Optional, Literal
# from pydantic import BaseModel, Field
# import fitz  # PyMuPDF
# from dotenv import load_dotenv
#
# import sys
# from pathlib import Path
# root_path = Path(__file__).resolve().parents[3]
# if str(root_path) not in sys.path:
#     sys.path.insert(0, str(root_path))
#
# from src.clients.client_llm import LLMClient
#
#
# load_dotenv()
#
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)s | %(message)s",
# )
# logger = logging.getLogger("cv-matcher.parser")
#
# CV_DIR = Path(__file__).parent.parent.parent.parent / "proyectos/cv-matcher/data/cvs_anonimizados"
# CV_DIR.mkdir(parents=True, exist_ok=True)
#
# JD_DIR = Path(__file__).parent.parent.parent.parent / "proyectos/cv-matcher/data/job_descriptions"
# JD_DIR.mkdir(parents=True, exist_ok=True)
#
#
# # ============================================================
# # SECCIÓN 1: Schemas Pydantic para CV Matcher
# # ============================================================
#
# class Idioma(BaseModel):
#     """Representa el dominio de un idioma por parte del candidato."""
#     idioma: str = Field(description="Nombre del idioma (ej: Inglés, Francés)")
#     nivel: str = Field(description="Nivel alcanzado (ej: B2, Nativo, Avanzado)")
#
#
# class CVEstructurado(BaseModel):
#     """
#     Representa la información profesional extraída y estructurada de un Curriculum Vitae.
#
#     Su función principal es servir como un contenedor de datos limpio y tipado que facilita
#     el procesamiento posterior, como la indexación en bases de datos vectoriales (RAG)
#     o el emparejamiento con ofertas laborales, eliminando cualquier dato de carácter
#     personal para cumplir con normativas de privacidad.
#
#     NOTA CRÍTICA DE PRIVACIDAD:
#     Los campos 'nombre', 'dni', 'telefono', 'email' y 'direccion'
#     NO se almacenan aquí. Solo se guardan datos profesionales.
#     El ID de candidato es un UUID interno.
#     """
#     candidato_id: str = Field(
#         description="UUID interno del candidato (sin relación al documento original)"
#     )
#     nivel_experiencia: Literal["junior", "semi-senior", "senior", "lead"] = Field(
#         description="Nivel inferido del total de años de experiencia"
#     )
#     anos_experiencia: float = Field(
#         ge=0,
#         description="Total de años de experiencia profesional estimados"
#     )
#     skills_tecnicos: list[str] = Field(
#         description="Lista de tecnologías, herramientas y habilidades técnicas"
#     )
#     skills_blandos: list[str] = Field(
#         description="Habilidades interpersonales y de gestión mencionadas"
#     )
#     industrias: list[str] = Field(
#         description="Sectores donde ha trabajado (banca, retail, minería, etc.)"
#     )
#     cargos_anteriores: list[str] = Field(
#         description="Lista de títulos de cargo (sin empresa ni fechas exactas)"
#     )
#     nivel_educacion: Literal["tecnico", "bachiller", "licenciado", "magister", "doctor"]
#     carreras: list[str] = Field(
#         description="Carreras o especialidades estudiadas"
#     )
#     certificaciones: list[str] = Field(
#         default_factory=list,
#         description="Certificaciones profesionales (AWS, PMP, CPA, etc.)"
#     )
#     idiomas: list[Idioma] = Field(
#         description="Lista de idiomas y sus niveles"
#     )
#     resumen_perfil: str = Field(
#         description="Resumen objetivo del perfil profesional en 2-3 oraciones"
#     )
#
#
# class JobDescription(BaseModel):
#     """
#     Representa la estructura formal de una descripción de puesto de trabajo (Job Description).
#
#     Esta clase se utiliza para estandarizar los requisitos de una oferta laboral, permitiendo
#     extraer de forma sistemática los skills técnicos, blandos, años de experiencia y nivel
#     educativo requeridos. Facilita la comparación objetiva entre el perfil de un candidato
#     y las necesidades reales del puesto.
#     """
#     jd_id: str = Field(description="UUID interno de la oferta de trabajo")
#     titulo_puesto: str = Field(description="Nombre del cargo o posición")
#     nivel_requerido: Literal["junior", "semi-senior", "senior", "lead"] = Field(
#         description="Nivel de seniority buscado"
#     )
#     anos_experiencia_min: float = Field(description="Años mínimos de experiencia requerida")
#     skills_requeridos: list[str] = Field(description="Habilidades obligatorias (must-have)")
#     skills_deseables: list[str] = Field(description="Habilidades valoradas (nice-to-have)")
#     industria_preferida: list[str] = Field(description="Sectores de experiencia deseados")
#     nivel_educacion_minimo: str = Field(description="Grado académico mínimo requerido")
#     idiomas_requeridos: list[Idioma] = Field(description="Lista de idiomas y niveles mínimos")
#     descripcion_rol: str = Field(description="Descripción textual de las responsabilidades")
#
#
# # ============================================================
# # SECCIÓN 2: Anonimizador de CVs
# # ============================================================
#
# class CVAnonymizer:
#     """
#     Clase encargada de la desidentificación de datos sensibles en documentos de CV.
#
#     Su función es localizar y reemplazar Información de Identificación Personal (PII)
#     como DNI, números de teléfono, correos electrónicos y nombres propios por etiquetas
#     genéricas. Esto garantiza el cumplimiento de leyes de protección de datos (como la
#     Ley 29733 en Perú) y reduce el sesgo algorítmico durante el proceso de selección.
#
#     # Conceptos clave:
#     # ----------------
#     # PII (Personally Identifiable Information): Datos que permiten identificar a una persona.
#     # NER (Named Entity Recognition): Técnica para identificar entidades como nombres en texto.
#     # HEURÍSTICA: Es una regla práctica o "atajo" lógico que suele funcionar bien en la
#     #             mayoría de los casos, aunque no garantiza el 100% de precisión.
#     """
#
#     # Patrones para PII peruana usando expresiones regulares (Regex)
#     # La librería 're' se utiliza para compilar estos patrones (re.compile)
#     # para que las búsquedas sean mucho más rápidas y eficientes en textos largos.
#
#     # PATRON_DNI: Busca exactamente 8 dígitos (\d{8}) entre límites de palabra (\b)
#     PATRON_DNI = re.compile(r"\b\d{8}\b")
#
#     # PATRON_RUC: Busca exactamente 11 dígitos (\d{11}) entre límites de palabra (\b)
#     PATRON_RUC = re.compile(r"\b\d{11}\b")
#
#     # PATRON_TELEFONO: Busca números celulares (9 + 8 dígitos) o fijos (7 u 8 dígitos).
#     # Opcionalmente captura el prefijo de país (+51).
#     PATRON_TELEFONO = re.compile(r"\b(?:\+51\s?)?(?:9\d{8}|\d{7,8})\b")
#
#     # PATRON_EMAIL: Identifica el formato estándar de un correo electrónico:
#     # usuario@dominio.tld con caracteres comunes (letras, números, puntos, etc.).
#     PATRON_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
#
#     # Lista simple de nombres peruanos comunes (en producción usar NER)
#     INDICADORES_NOMBRE = ["nombres:", "nombre:", "apellidos:", "apellido:"]
#
#     def anonimizar_texto(self, texto: str) -> str:
#         """
#         Detecta y ofusca datos personales en una cadena de texto.
#
#         Este metodo aplica una serie de sustituciones basadas en expresiones regulares
#         para reemplazar correos, teléfonos, DNI y RUC por etiquetas informativas
#         (ej: [DNI_REDACTADO]). También aplica una HEURÍSTICA (una regla práctica basada
#         en la estructura común de los CVs) para detectar y anonimizar el nombre del
#         candidato si aparece al inicio del documento.
#
#         Args:
#             texto (str): El contenido textual original del CV.
#
#         Returns:
#             str: El texto anonimizado listo para ser procesado por un LLM o almacenado.
#         """
#         texto = self.PATRON_EMAIL.sub("[EMAIL_REDACTADO]", texto)
#         texto = self.PATRON_DNI.sub("[DNI_REDACTADO]", texto)
#         texto = self.PATRON_RUC.sub("[RUC_REDACTADO]", texto)
#         texto = self.PATRON_TELEFONO.sub("[TELEFONO_REDACTADO]", texto)
#
#         # Eliminar la primera línea si parece ser el nombre del candidato
#         lineas = texto.split("\n")
#         if lineas and len(lineas[0].split()) <= 5:
#             # Primera línea corta, probablemente es el nombre
#             lineas[0] = "[NOMBRE_REDACTADO]"
#
#         return "\n".join(lineas)
#
#
# # ============================================================
# # SECCIÓN 3: Extractor estructurado de CVs
# # ============================================================
#
# class CVParser:
#     """
#     Clase encargada de orquestar el pipeline completo de procesamiento de Curriculums Vitae.
#
#     Su función es transformar archivos físicos (PDF, DOCX) o texto bruto en objetos
#     'CVEstructurado' validados. El proceso incluye la extracción de texto, la
#     anonimización de datos sensibles mediante 'CVAnonymizer' y la extracción de
#     información profesional utilizando un LLM.
#     """
#
#     def __init__(self):
#         self.anonymizer = CVAnonymizer()
#         self.cliente = LLMClient(
#             modelo="gpt-4o-mini",     # Económico para procesamiento masivo
#             temperatura=0.0,
#             max_tokens=1200,
#         )
#
#     def _extraer_texto_pdf(self, ruta: Path) -> str:
#         """
#         Extrae el contenido textual de un archivo PDF utilizando PyMuPDF.
#
#         Args:
#             ruta (Path): Ruta al archivo PDF.
#
#         Returns:
#             str: Texto extraído de todas las páginas del documento.
#         """
#         doc = fitz.open(ruta)
#         texto = "\n".join(pagina.get_text("text") for pagina in doc)
#         doc.close()
#         return texto
#
#     def _extraer_texto_docx(self, ruta: Path) -> str:
#         """
#         Extrae el contenido textual de un archivo DOCX utilizando python-docx.
#
#         Args:
#             ruta (Path): Ruta al archivo DOCX.
#
#         Returns:
#             str: Texto extraído de los párrafos del documento.
#         """
#         try:
#             from docx import Document
#             doc = Document(ruta)
#             return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
#         except ImportError:
#             logger.warning("python-docx no instalado. pip install python-docx")
#             return ""
#
#     def parsear_texto_cv(self, texto_crudo: str) -> CVEstructurado:
#         """
#         Procesa texto bruto de un CV para convertirlo en una estructura objetiva.
#
#         Aplica anonimización para eliminar PII (Información de Identificación Personal)
#         y luego utiliza el LLM para identificar experiencia, skills y educación.
#
#         Args:
#             texto_crudo (str): El texto original extraído del CV.
#
#         Returns:
#             CVEstructurado: Objeto con la información profesional extraída y validada.
#         """
#         # Paso 1: Anonimizar (Aplica lógica heurística para proteger la privacidad)
#         texto_anonimizado = self.anonymizer.anonimizar_texto(texto_crudo)
#
#         # Paso 2: Extraer estructura con LLM
#         system_prompt = """Eres un analizador experto de CVs para el mercado laboral peruano.
# Extrae información profesional del CV de forma objetiva y estructurada.
# NUNCA incluyas nombre completo, DNI, teléfono, email ni dirección en tu respuesta.
# Enfócate en competencias, experiencia y formación profesional."""
#
#         user_message = f"""Analiza este CV y extrae la información estructurada:
#
# {texto_anonimizado[:3000]}
#
# El 'candidato_id' debe ser exactamente: "{uuid.uuid4()}"
# """
#         cv_estructurado = self.cliente.llamar(
#             system_prompt=system_prompt,
#             user_message=user_message,
#             schema=CVEstructurado,
#         )
#
#         logger.info(f"CV_ESTRUCTURADO (Data): {cv_estructurado.model_dump()}")
#         logger.info(f"CV_ESTRUCTURADO (Metadatos): {cv_estructurado.__class__.model_fields}")
#         logger.info(f"CV_ESTRUCTURADO Métodos disponibles: {dir(cv_estructurado)}")
#
#         return cv_estructurado
#
#     def parsear_archivo_cv(self, ruta: Path) -> CVEstructurado:
#         """
#         Lee un archivo de CV y lo procesa a través del pipeline completo.
#
#         Identifica el formato del archivo (PDF o DOCX), extrae el texto y llama
#         al proceso de estructuración.
#
#         Args:
#             ruta (Path): Ubicación del archivo del CV.
#
#         Returns:
#             CVEstructurado: Resultado del procesamiento estructurado.
#         """
#         # Paso 1: Extraer texto según formato
#         if ruta.suffix.lower() == ".pdf":
#             texto_crudo = self._extraer_texto_pdf(ruta)
#         elif ruta.suffix.lower() in [".docx", ".doc"]:
#             texto_crudo = self._extraer_texto_docx(ruta)
#         else:
#             # Si es texto plano o formato desconocido, intentamos leer como texto
#             try:
#                 texto_crudo = ruta.read_text(encoding="utf-8")
#             except Exception:
#                 raise ValueError(f"Formato no soportado o error al leer: {ruta.suffix}")
#
#         return self.parsear_texto_cv(texto_crudo)
#
#     def parsear_cv(self, ruta: Path) -> CVEstructurado:
#         """
#         Metodo legacy para mantener compatibilidad con versiones anteriores.
#         Delega la funcionalidad a parsear_archivo_cv.
#         """
#         return self.parsear_archivo_cv(ruta)
#
#
# # ============================================================
# # SECCIÓN 4: Parser de Job Descriptions
# # ============================================================
#
# class JDParser:
#     """
#     Clase encargada de extraer y estructurar información de descripciones de puesto (Job Descriptions).
#
#     Su función es transformar textos de ofertas laborales (a menudo desestructurados)
#     en objetos 'JobDescription' validados, extrayendo requisitos técnicos, años de
#     experiencia y niveles de seniority para facilitar el matching con candidatos.
#     """
#
#     def __init__(self):
#         self.cliente = LLMClient(
#             modelo="gpt-4o-mini",
#             temperatura=0.0,
#             max_tokens=800,
#         )
#
#     def _extraer_texto_pdf(self, ruta: Path) -> str:
#         """Extrae texto de una JD en PDF."""
#         doc = fitz.open(ruta)
#         texto = "\n".join(pagina.get_text("text") for pagina in doc)
#         doc.close()
#         return texto
#
#     def _extraer_texto_docx(self, ruta: Path) -> str:
#         """Extrae texto de una JD en DOCX."""
#         try:
#             from docx import Document
#             doc = Document(ruta)
#             return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
#         except ImportError:
#             logger.warning("python-docx no instalado. pip install python-docx")
#             return ""
#
#     def parsear_jd(self, texto_jd: str, titulo: str = "Puesto sin título") -> JobDescription:
#         """
#         Analiza el contenido de una JD y lo convierte en un objeto estructurado.
#
#         Utiliza el parámetro 'titulo' proporcionado como contexto adicional para el LLM
#         en caso de que el texto de la JD sea ambiguo sobre el cargo.
#
#         Args:
#             texto_jd (str): El contenido textual de la oferta laboral.
#             titulo (str): Título sugerido o conocido del puesto.
#
#         Returns:
#             JobDescription: Instancia de Pydantic con los datos extraídos y validados.
#         """
#         system_prompt = """Eres un analizador experto de ofertas de empleo del mercado peruano.
# Extrae los requisitos del puesto de forma clara y estructurada.
# Distingue entre skills obligatorios (must-have) y deseables (nice-to-have)."""
#
#         user_message = f"""Analiza esta Job Description y extrae la información estructurada.
# Usa el siguiente título como referencia si es necesario: "{titulo}"
#
# Contenido de la JD:
# {texto_jd[:4000]}
#
# El 'jd_id' debe ser exactamente: "{uuid.uuid4()}"
# """
#         jd_estructurada = self.cliente.llamar(
#             system_prompt=system_prompt,
#             user_message=user_message,
#             schema=JobDescription,
#         )
#
#         logger.info(f"JD_ESTRUCTURADA (Data): {jd_estructurada.model_dump()}")
#         logger.info(f"JD_ESTRUCTURADA (Metadatos): {jd_estructurada.__class__.model_fields}")
#         logger.info(f"JD_ESTRUCTURADA Métodos disponibles: {dir(jd_estructurada)}")
#
#         # Si el LLM no extrajo un título o es muy genérico, usamos el título proporcionado
#         if not jd_estructurada.titulo_puesto or jd_estructurada.titulo_puesto == "Puesto sin título":
#             jd_estructurada.titulo_puesto = titulo
#
#         return jd_estructurada
#
#     def parsear_archivo_jd(self, ruta: Path, titulo: Optional[str] = None) -> JobDescription:
#         """
#         Lee un archivo (PDF/DOCX/TXT) y lo procesa como una Job Description.
#
#         Args:
#             ruta (Path): Ubicación del archivo de la JD.
#             titulo (Optional[str]): Título opcional para ayudar al parser.
#
#         Returns:
#             JobDescription: El resultado del procesamiento estructurado.
#         """
#         if not titulo:
#             titulo = ruta.stem.replace("-", " ").replace("_", " ").title()
#
#         if ruta.suffix.lower() == ".pdf":
#             texto_jd = self._extraer_texto_pdf(ruta)
#         elif ruta.suffix.lower() in [".docx", ".doc"]:
#             texto_jd = self._extraer_texto_docx(ruta)
#         else:
#             texto_jd = ruta.read_text(encoding="utf-8")
#
#         return self.parsear_jd(texto_jd, titulo)
#
#
# if __name__ == "__main__":
#     print("=" * 60)
#     print("LAB01-03 — Parser de CVs y JDs (CV Matcher)")
#     print("=" * 60)
#
#     # ── DEMO 1: Parsear CV de ejemplo ─────────────────────────
#     print("\n📋 PRUEBA 1: Parsear CV de ejemplo")
#     print("-" * 40)
#
#     CV_EJEMPLO = """
# Juan Carlos Pérez Rodríguez
# DNI: 47123456 | Teléfono: 987654321 | juan.perez@gmail.com
# Jr. Los Álamos 123, Miraflores, Lima
#
# PERFIL PROFESIONAL
# Desarrollador Backend con 4 años de experiencia en Python y Django.
# Especializado en APIs REST y microservicios para el sector financiero.
#
# EXPERIENCIA LABORAL
# 2021 - Actualidad: Desarrollador Backend Senior — Banco de Crédito del Perú
# - Desarrollo de APIs REST con Python/Django para app móvil (2M usuarios)
# - Migración de monolito a microservicios con Docker y Kubernetes
# - Integración con SUNAT para validación de facturas electrónicas
#
# 2019 - 2021: Desarrollador Backend — Startup Fintech (Lima)
# - Desarrollo de plataforma de pagos con FastAPI y PostgreSQL
# - Implementación de sistema de notificaciones con Celery + Redis
#
# EDUCACIÓN
# 2014 - 2019: Ingeniería de Sistemas — Universidad Nacional Mayor de San Marcos
# 2023: AWS Certified Solutions Architect - Associate
#
# HABILIDADES TÉCNICAS
# Python, Django, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, Git, AWS
#
# IDIOMAS
# Español: Nativo | Inglés: B2 (TOEFL 95)
# """
#
#     # Crear archivo demo
#     ruta_demo = CV_DIR / "cv_demo.txt"
#     ruta_demo.write_text(CV_EJEMPLO, encoding="utf-8")
#
#     try:
#         cv_parser = CVParser()
#
#         # Prueba 1: Parsear desde texto directamente
#         print("👉 Probando parsear_texto_cv (desde texto)...")
#         # Nota: En un entorno real esto llamaría al LLM
#         # Para la demo, mostramos la anonimización que es el paso previo
#         texto_anon = cv_parser.anonymizer.anonimizar_texto(CV_EJEMPLO)
#         print("✅ Texto anonimizado (Primeras líneas):")
#         print("\n".join(texto_anon.splitlines()[:5]))
#
#         # Prueba 2: Parsear desde archivo
#         print("\n👉 Probando parsear_archivo_cv (desde archivo)...")
#         cv = cv_parser.parsear_archivo_cv(ruta_demo) # Descomentar si hay API KEY
#         print(f"   Archivo preparado en: {ruta_demo}")
#
#     except Exception as e:
#         print(f"❌ Error: {e}")
#
#     # ── DEMO 2: Parsear Job Description ───────────────────────
#     print("\n📋 PRUEBA 2: Parsear Job Description")
#     print("-" * 40)
#
#     JD_EJEMPLO = """
# POSICIÓN: Desarrollador Backend Python — Senior
# Empresa: Fintech Lima SAC
#
# REQUISITOS OBLIGATORIOS:
# - 4+ años con Python (Django o FastAPI)
# - Experiencia en PostgreSQL y Redis
# - Conocimiento de APIs REST y microservicios
# - Inglés B2 mínimo
#
# REQUISITOS DESEABLES:
# - Experiencia con Kubernetes o Docker
# - Conocimiento de AWS o GCP
# - Experiencia en sector financiero o fintech peruano
#
# OFRECEMOS:
# - Trabajo remoto
# - S/ 8,000 - S/ 12,000 mensual
# """
#
#     # Crear archivo demo para JD
#     ruta_jd_demo = JD_DIR / "jd_demo.txt"
#     ruta_jd_demo.write_text(JD_EJEMPLO, encoding="utf-8")
#
#     try:
#         jd_parser = JDParser()
#
#         # Prueba 1: Parsear desde texto directamente
#         print("👉 Probando parsear_jd (desde texto)...")
#         jd = jd_parser.parsear_jd(JD_EJEMPLO, "Desarrollador Backend Python Senior")
#
#         print("✅ JD parseada (Texto):")
#         print(f"   Título: {jd.titulo_puesto}")
#         print(f"   Nivel requerido: {jd.nivel_requerido}")
#
#         # Prueba 2: Parsear desde archivo
#         print("\n👉 Probando parsear_archivo_jd (desde archivo)...")
#         jd_file = jd_parser.parsear_archivo_jd(ruta_jd_demo)
#         print("✅ JD parseada (Archivo):")
#         print(f"   Título: {jd_file.titulo_puesto}")
#         print(f"   Skills obligatorios: {', '.join(jd_file.skills_requeridos[:5])}")
#
#         # Guardar JD estructurada
#         jd_path = JD_DIR / "backend-python-senior.json"
#         with open(jd_path, "w", encoding="utf-8") as f:
#             json.dump(jd_file.model_dump(), f, ensure_ascii=False, indent=2)
#         print(f"\n   Guardada en: {jd_path}")
#
#     except Exception as e:
#         print(f"❌ Error (¿API key configurada?): {e}")
#
#     print("\n" + "=" * 60)
#     print("✅ Lab completado.")
#     print("Los JSONs generados son el input del RAG en el Módulo 02.")
#     print("=" * 60)
