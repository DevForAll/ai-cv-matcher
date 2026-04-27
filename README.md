# AI CV Matcher

Pipeline de procesamiento de CVs y ofertas laborales usando LLMs. Extrae, anonimiza y estructura información profesional de documentos en PDF, DOCX y TXT, preparando los datos para sistemas de matching basados en RAG.

## Descripcion

AI CV Matcher automatiza el análisis de currículums y descripciones de puesto (Job Descriptions) orientado al mercado laboral peruano. Utiliza modelos de lenguaje (OpenAI GPT-4o-mini o Google Gemini) para extraer información estructurada y validada mediante esquemas Pydantic, eliminando datos personales (PII) antes de cualquier procesamiento.

### Funcionalidades

- **Anonimización de PII**: Detecta y redacta DNI, RUC, teléfono, email y nombre del candidato usando regex adaptadas al formato peruano (Ley 29733).
- **Parsing de CVs**: Transforma archivos PDF, DOCX o TXT en objetos `CVEstructurado` con skills, experiencia, educación, certificaciones e idiomas.
- **Parsing de Job Descriptions**: Analiza ofertas laborales y extrae requisitos técnicos, nivel de seniority, años de experiencia y skills obligatorios vs. deseables.
- **Cliente LLM unificado**: Interfaz común para OpenAI y Google Gemini con reintentos automáticos (exponential backoff), conteo de tokens y soporte para Structured Outputs (Pydantic).
- **Preparación para RAG**: Los objetos estructurados son el input del pipeline de indexación vectorial (Módulo 02 — próximamente).

## Estructura del proyecto

```
ai-cv-matcher/
├── src/
│   ├── clients/
│   │   └── client_llm.py       # Cliente unificado OpenAI / Google Gemini
│   ├── models/
│   │   └── schemas.py          # Schemas Pydantic: CVEstructurado, JobDescription
│   ├── tools/
│   │   ├── cv_anonymizer.py    # Anonimizador de PII (regex)
│   │   ├── cv_parser.py        # Parser de CVs (PDF / DOCX / TXT -> CVEstructurado)
│   │   └── jd_parser.py        # Parser de JDs (PDF / DOCX / TXT -> JobDescription)
│   └── rag/
│       └── pipeline.py         # Pipeline de demostración (CV + JD)
├── data/
│   ├── cvs_anonimizados/       # CVs de entrada (PDF, DOCX, TXT)
│   └── job_descriptions/       # JDs de entrada y JSONs generados
├── .env.example                # Variables de entorno requeridas (plantilla)
├── pyproject.toml              # Configuración del proyecto (uv)
├── requirements.txt            # Dependencias para instalación con pip
└── uv.lock                     # Lock file reproducible (uv)
```

## Requisitos

- Python **3.12** o superior
- API key de **OpenAI** y/o **Google Gemini** (al menos una)

## Instalacion

### Con uv (recomendado)

```bash
# 1. Clonar el repositorio
git clone https://github.com/DevForAll/ai-cv-matcher.git
cd ai-cv-matcher

# 2. Instalar uv si no lo tienes
pip install uv

# 3. Crear el entorno virtual e instalar dependencias (usa uv.lock para versiones exactas)
uv sync

# 4. Configurar variables de entorno
cp .env.example .env
# Abrir .env y completar con tus API keys
```

### Con pip

```bash
# 1. Clonar el repositorio
git clone https://github.com/DevForAll/ai-cv-matcher.git
cd ai-cv-matcher

# 2. Crear entorno virtual
python -m venv .venv

# Activar en Linux/Mac:
source .venv/bin/activate

# Activar en Windows:
.venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Abrir .env y completar con tus API keys
```

## Configuracion

Crea el archivo `.env` en la raíz del proyecto a partir de la plantilla:

```bash
cp .env.example .env
```

Contenido del `.env`:

```env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
```

> Solo necesitas configurar la key del proveedor que vayas a usar. Por defecto el sistema usa **OpenAI (gpt-4o-mini)**.

## Uso

### Pipeline de demostración completo

```bash
# Con uv:
uv run python src/rag/pipeline.py

# Con pip (entorno virtual activado):
python src/rag/pipeline.py
```

El pipeline ejecuta dos demos:

1. **Demo CV** — Anonimiza un CV de ejemplo y extrae `CVEstructurado` via LLM.
2. **Demo JD** — Parsea una Job Description y genera un JSON con los requisitos del puesto.

### Usar los módulos individualmente

```python
from pathlib import Path
from src.tools.cv_anonymizer import CVAnonymizer
from src.tools.cv_parser import CVParser
from src.tools.jd_parser import JDParser

# Anonimizar texto de un CV
anonymizer = CVAnonymizer()
texto_limpio = anonymizer.anonimizar_texto(texto_cv)

# Parsear un CV desde archivo (PDF, DOCX o TXT)
cv_parser = CVParser()
cv = cv_parser.parsear_archivo_cv(Path("data/cvs_anonimizados/mi_cv.pdf"))
print(cv.model_dump_json(indent=2))

# Parsear una Job Description
jd_parser = JDParser()
jd = jd_parser.parsear_archivo_jd(Path("data/job_descriptions/mi_jd.pdf"))
print(jd.titulo_puesto)
print(jd.skills_requeridos)
```

### Agregar archivos para procesar

| Tipo | Directorio | Formatos soportados |
|---|---|---|
| CVs | `data/cvs_anonimizados/` | `.pdf`, `.docx`, `.doc`, `.txt` |
| Job Descriptions | `data/job_descriptions/` | `.pdf`, `.docx`, `.doc`, `.txt` |

## Datos de salida

### CVEstructurado

| Campo | Tipo | Descripción |
|---|---|---|
| `candidato_id` | `str` | UUID interno (sin PII) |
| `nivel_experiencia` | `junior / semi-senior / senior / lead` | Nivel inferido por el LLM |
| `anos_experiencia` | `float` | Total de años estimados |
| `skills_tecnicos` | `list[str]` | Tecnologías y herramientas |
| `skills_blandos` | `list[str]` | Habilidades interpersonales |
| `industrias` | `list[str]` | Sectores de experiencia |
| `cargos_anteriores` | `list[str]` | Títulos de cargo (sin empresa ni fechas) |
| `nivel_educacion` | `str` | Grado académico mínimo |
| `carreras` | `list[str]` | Carreras o especialidades |
| `certificaciones` | `list[str]` | Certificaciones profesionales |
| `idiomas` | `list[Idioma]` | Idiomas y niveles (ej: Inglés B2) |
| `resumen_perfil` | `str` | Resumen profesional en 2-3 oraciones |

### JobDescription

| Campo | Tipo | Descripción |
|---|---|---|
| `jd_id` | `str` | UUID interno de la oferta |
| `titulo_puesto` | `str` | Nombre del cargo |
| `nivel_requerido` | `junior / semi-senior / senior / lead` | Seniority buscado |
| `anos_experiencia_min` | `float` | Años mínimos requeridos |
| `skills_requeridos` | `list[str]` | Habilidades obligatorias (must-have) |
| `skills_deseables` | `list[str]` | Habilidades valoradas (nice-to-have) |
| `industria_preferida` | `list[str]` | Sectores de experiencia deseados |
| `nivel_educacion_minimo` | `str` | Grado académico mínimo |
| `idiomas_requeridos` | `list[Idioma]` | Idiomas y niveles mínimos |
| `descripcion_rol` | `str` | Descripción de responsabilidades |

## Privacidad

El anonimizador redacta automáticamente antes de enviar cualquier dato al LLM:

| Dato | Patrón detectado |
|---|---|
| Nombre | Primera línea corta del documento (heurística) |
| DNI | Exactamente 8 dígitos consecutivos |
| RUC | Exactamente 11 dígitos consecutivos |
| Teléfono | Formato peruano (celular 9XXXXXXXX o fijo, con/sin +51) |
| Email | Formato estándar usuario@dominio.tld |

Ningún dato personal llega al LLM ni se almacena en los objetos de salida.

## Dependencias principales

| Librería | Versión | Uso |
|---|---|---|
| `openai` | >=2.32.0 | Cliente OpenAI con Structured Outputs |
| `google-generativeai` | >=0.8.6 | Cliente Google Gemini |
| `pydantic` | >=2.13.3 | Schemas y validación de salida |
| `pymupdf` | >=1.27.2.3 | Extracción de texto desde PDF |
| `python-dotenv` | >=1.2.2 | Carga de variables de entorno |
| `tiktoken` | >=0.12.0 | Conteo de tokens (estimación de costos) |

## Roadmap

- [ ] Módulo 02: Indexación vectorial con Qdrant
- [ ] Matching CV vs JD con scoring cuantitativo
- [ ] API REST con FastAPI
- [ ] NER avanzado para detección de nombres (reemplazar heurística actual)
- [ ] Soporte para múltiples idiomas y mercados laborales
