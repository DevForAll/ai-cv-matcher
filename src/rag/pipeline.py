from pathlib import Path

from tools.cv_parser import CVParser
from tools.jd_parser import JDParser

import json

CV_DIR = Path(__file__).parent.parent.parent.parent / "ai-cv-matcher/data/cvs_anonimizados"
CV_DIR.mkdir(parents=True, exist_ok=True)

JD_DIR = Path(__file__).parent.parent.parent.parent / "ai-cv-matcher/data/job_descriptions"
JD_DIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    print("=" * 60)
    print("LAB01-03 — Parser de CVs y JDs (CV Matcher)")
    print("=" * 60)

    # ── DEMO 1: Parsear CV de ejemplo ─────────────────────────
    print("\n📋 PRUEBA 1: Parsear CV de ejemplo")
    print("-" * 40)

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

    # Crear archivo demo
    ruta_demo = CV_DIR / "cv_demo.txt"
    ruta_demo.write_text(CV_EJEMPLO, encoding="utf-8")

    try:
        cv_parser = CVParser()

        # Prueba 1: Parsear desde texto directamente
        print("👉 Probando parsear_texto_cv (desde texto)...")
        # Nota: En un entorno real esto llamaría al LLM
        # Para la demo, mostramos la anonimización que es el paso previo
        texto_anon = cv_parser.anonymizer.anonimizar_texto(CV_EJEMPLO)
        print("✅ Texto anonimizado (Primeras líneas):")
        print("\n".join(texto_anon.splitlines()[:5]))

        # Prueba 2: Parsear desde archivo
        print("\n👉 Probando parsear_archivo_cv (desde archivo)...")
        cv = cv_parser.parsear_archivo_cv(ruta_demo) # Descomentar si hay API KEY
        print(f"   Archivo preparado en: {ruta_demo}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # ── DEMO 2: Parsear Job Description ───────────────────────
    print("\n📋 PRUEBA 2: Parsear Job Description")
    print("-" * 40)

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

    # Crear archivo demo para JD
    ruta_jd_demo = JD_DIR / "jd_demo.txt"
    ruta_jd_demo.write_text(JD_EJEMPLO, encoding="utf-8")

    try:
        jd_parser = JDParser()

        # Prueba 1: Parsear desde texto directamente
        print("👉 Probando parsear_jd (desde texto)...")
        jd = jd_parser.parsear_jd(JD_EJEMPLO, "Desarrollador Backend Python Senior")

        print("✅ JD parseada (Texto):")
        print(f"   Título: {jd.titulo_puesto}")
        print(f"   Nivel requerido: {jd.nivel_requerido}")

        # Prueba 2: Parsear desde archivo
        print("\n👉 Probando parsear_archivo_jd (desde archivo)...")
        jd_file = jd_parser.parsear_archivo_jd(ruta_jd_demo)
        print("✅ JD parseada (Archivo):")
        print(f"   Título: {jd_file.titulo_puesto}")
        print(f"   Skills obligatorios: {', '.join(jd_file.skills_requeridos[:5])}")

        # Guardar JD estructurada
        jd_path = JD_DIR / "backend-python-senior.json"
        with open(jd_path, "w", encoding="utf-8") as f:
            json.dump(jd_file.model_dump(), f, ensure_ascii=False, indent=2)
        print(f"\n   Guardada en: {jd_path}")

    except Exception as e:
        print(f"❌ Error (¿API key configurada?): {e}")

    print("\n" + "=" * 60)
    print("✅ Lab completado.")
    print("Los JSONs generados son el input del RAG en el Módulo 02.")
    print("=" * 60)
