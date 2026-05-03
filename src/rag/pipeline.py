import json
from pathlib import Path

from logger import LogContext, get_logger, setup_logging
from tools.cv_parser import CVParser
from tools.jd_parser import JDParser

setup_logging()
logger = get_logger(__name__)

CV_DIR = (
    Path(__file__).parent.parent.parent.parent / "ai-cv-matcher/data/cvs_anonimizados"
)
CV_DIR.mkdir(parents=True, exist_ok=True)

JD_DIR = (
    Path(__file__).parent.parent.parent.parent / "ai-cv-matcher/data/job_descriptions"
)
JD_DIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    logger.info("LAB01-03 — Parser de CVs y JDs (CV Matcher)")

    # ── DEMO 1: Parsear CV de ejemplo ─────────────────────────────────────────
    with LogContext("demo-cv") as cid:
        logger.info("DEMO 1: Parsear CV de ejemplo")

        CV_EJEMPLO = """
Juan Carlos Pérez Rodríguez
DNI: 47123456 | Teléfono: 987654321 | juan.perez@gmail.com
Jr. Los Álamos 123, Miraflores, Lima

PERFIL PROFESIONAL
Desarrollador Backend con 4 años de experiencia en Python y Django.
Especializado en APIs REST y microservicios para el sector financiero.

EXPERIENCIA LABORAL
2021 - Actualidad: Desarrollador Backend Senior — Banco de Crédito del Perú
- Desarrollo de APIs REST con Python/Django para app móvil (2M usuarios)
- Migración de monolito a microservicios con Docker y Kubernetes
- Integración con SUNAT para validación de facturas electrónicas

2019 - 2021: Desarrollador Backend — Startup Fintech (Lima)
- Desarrollo de plataforma de pagos con FastAPI y PostgreSQL
- Implementación de sistema de notificaciones con Celery + Redis

EDUCACIÓN
2014 - 2019: Ingeniería de Sistemas — Universidad Nacional Mayor de San Marcos
2023: AWS Certified Solutions Architect - Associate

HABILIDADES TÉCNICAS
Python, Django, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, Git, AWS

IDIOMAS
Español: Nativo | Inglés: B2 (TOEFL 95)
"""

        ruta_demo = CV_DIR / "cv_demo.txt"
        ruta_demo.write_text(CV_EJEMPLO, encoding="utf-8")

        try:
            cv_parser = CVParser()

            logger.info("Probando anonimización (parsear_texto_cv)...")
            texto_anon = cv_parser.anonymizer.anonimizar_texto(CV_EJEMPLO)
            preview = "\n".join(texto_anon.splitlines()[:5])
            logger.info("Texto anonimizado (primeras líneas):\n%s", preview)

            logger.info("Probando parsear_archivo_cv desde archivo...")
            cv = cv_parser.parsear_archivo_cv(ruta_demo)
            logger.info("CV parseado correctamente", extra={"archivo": str(ruta_demo)})

        except Exception as e:
            logger.exception("Error en Demo 1: %s", e)

    # ── DEMO 2: Parsear Job Description ───────────────────────────────────────
    with LogContext("demo-jd") as cid:
        logger.info("DEMO 2: Parsear Job Description")

        JD_EJEMPLO = """
POSICIÓN: Desarrollador Backend Python — Senior
Empresa: Fintech Lima SAC

REQUISITOS OBLIGATORIOS:
- 4+ años con Python (Django o FastAPI)
- Experiencia en PostgreSQL y Redis
- Conocimiento de APIs REST y microservicios
- Inglés B2 mínimo

REQUISITOS DESEABLES:
- Experiencia con Kubernetes o Docker
- Conocimiento de AWS o GCP
- Experiencia en sector financiero o fintech peruano

OFRECEMOS:
- Trabajo remoto
- S/ 8,000 - S/ 12,000 mensual
"""

        ruta_jd_demo = JD_DIR / "jd_demo.txt"
        ruta_jd_demo.write_text(JD_EJEMPLO, encoding="utf-8")

        try:
            jd_parser = JDParser()

            logger.info("Probando parsear_jd desde texto...")
            jd = jd_parser.parsear_jd(JD_EJEMPLO, "Desarrollador Backend Python Senior")
            logger.info(
                "JD parseada (texto)",
                extra={"titulo": jd.titulo_puesto, "nivel": jd.nivel_requerido},
            )

            logger.info("Probando parsear_archivo_jd desde archivo...")
            jd_file = jd_parser.parsear_archivo_jd(ruta_jd_demo)
            logger.info(
                "JD parseada (archivo)",
                extra={
                    "titulo": jd_file.titulo_puesto,
                    "skills_top5": jd_file.skills_requeridos[:5],
                },
            )

            jd_path = JD_DIR / "backend-python-senior.json"
            with open(jd_path, "w", encoding="utf-8") as f:
                json.dump(jd_file.model_dump(), f, ensure_ascii=False, indent=2)
            logger.info("JD guardada en: %s", jd_path)

        except Exception as e:
            logger.exception("Error en Demo 2 (¿API key configurada?): %s", e)

    logger.info("Lab completado. JSONs listos para el RAG en el Modulo 02.")
