# 👔 Proyecto: CV Matcher — Plataforma HR-Tech

> Contexto específico del proyecto. Lee también el CLAUDE.md raíz.

## Descripción del sistema

Sistema agéntico que recibe descripciones de puestos (JDs) y lotes de CVs,
genera un ranking semántico de candidatos, explica el razonamiento de cada
evaluación y puede conducir una entrevista inicial por chat. Orientado al
mercado laboral peruano (banca, servicios, tecnología).

## Arquitectura del sistema

```
Empresa → FastAPI Gateway
               ↓
          JD Processor          ← Extrae competencias requeridas del puesto
               ↓
          CV Ingestor           ← Parsea CVs (PDF/DOCX) → chunks → embeddings
               ↓
          Ranking Agent         ← LangGraph: busca en Qdrant + evalúa encaje
               ↓
          Bias Detector         ← Elimina criterios demográficos del score
               ↓
          Report Generator      ← Ranking explicable con justificación por CV
               ↓
         [Opcional] Interview Agent  ← Entrevista inicial por chat
```

## Stack técnico del proyecto

| Capa | Tecnología | Versión mínima |
|------|-----------|---------------|
| API Gateway | FastAPI | 0.111+ |
| Agente | LangGraph | 0.2+ |
| Vector DB | Qdrant | 1.9+ |
| Embeddings | text-embedding-3-large | OpenAI |
| LLM | GPT-4o / Gemini 1.5 Pro | latest |
| Parser CV | PyMuPDF + python-docx | - |
| Validación | PydanticAI | 0.0.13+ |
| Contenedor | Docker + Docker Compose | 24+ |
| Eval | Ragas + custom bias metrics | - |

## Estructura de carpetas del proyecto

```
cv-matcher/
├── CLAUDE.md
├── src/
│   ├── api/              ← Endpoints FastAPI
│   ├── agents/           ← Grafo LangGraph (ranking + interview)
│   ├── tools/            ← Herramientas (CV parser, JD extractor, searcher)
│   ├── rag/              ← Pipeline de ingesta de CVs y consulta semántica
│   ├── bias_detector/    ← Módulo de detección y eliminación de sesgo
│   └── models/           ← Schemas Pydantic (CV, JD, Ranking, Candidate)
├── data/
│   ├── cvs_anonimizados/ ← CVs de prueba sin PII (git-ignored)
│   ├── job_descriptions/ ← JDs de ejemplo por sector
│   └── competencias/     ← Catálogo de competencias del mercado peruano
├── docs/
│   ├── arquitectura.md
│   ├── etica-y-sesgo.md  ← Documento de política anti-discriminación
│   └── casos-de-uso.md
├── tests/
│   ├── test_ranking.py
│   ├── test_bias.py       ← Tests anti-sesgo obligatorios en CI
│   ├── test_parser.py
│   └── test_interview_agent.py
└── infra/
    ├── Dockerfile
    ├── docker-compose.yml
    └── .github/workflows/
```

## Datos de candidatos — Política de privacidad

- **NUNCA** almacenar nombre completo, DNI, dirección, teléfono o foto en la DB vectorial.
- Los CVs se anonimizar antes de indexar: `src/tools/cv_anonymizer.py`
- El ID del candidato es un UUID generado internamente, sin relación al documento original.
- Cumplimiento con Ley de Protección de Datos Personales (Ley 29733, Perú).

## Convenciones específicas del proyecto

- El score de un candidato es de 0.0 a 1.0 (similaridad semántica ponderada).
- El ranking SIEMPRE incluye justificación por cada criterio evaluado.
- Features prohibidas en el modelo de scoring:
  - Nombre, género inferido, edad, fotografía, dirección, universidad (pública/privada como criterio único).
- El `BiasDetector` actúa como capa de post-procesamiento sobre el score crudo.
- Cada evaluación se loguea para auditoría interna de sesgo.

## Seguridad — Reglas obligatorias

- **NUNCA** escribir API keys, tokens o contraseñas en el código fuente, ni siquiera como comentario o valor temporal.
- Todas las credenciales van exclusivamente en `.env` (está en `.gitignore`).
- El archivo `.env.example` solo puede contener claves vacías o con placeholder (`=` o `=sk-...`).
- Antes de sugerir cualquier código que use una API key, verificar que el valor se lee desde `os.getenv()` o `python-dotenv`.
- Si al revisar el código encuentras una clave hardcodeada, reemplázala por `os.getenv()` inmediatamente sin esperar instrucción.
- El proyecto usa `pre-commit` + `gitleaks` para bloquear commits con secretos. Si el hook falla, investigar antes de saltarlo.

## Comandos específicos

```bash
# Instalar en modo editable (una vez tras clonar o cambiar pyproject.toml)
uv pip install -e .

# Indexar lote de CVs
uv run python src/rag/ingest_cvs.py --source data/cvs_anonimizados/ --collection cv_embeddings

# Ejecutar ranking para una JD
uv run python src/agents/ranking_agent.py --jd data/job_descriptions/dev-backend.json

# Tests de sesgo (obligatorios antes de deploy)
uv run pytest tests/test_bias.py -v --tb=long

# Anonimizar CVs nuevos
uv run python src/tools/cv_anonymizer.py --input raw_cvs/ --output data/cvs_anonimizados/
```
