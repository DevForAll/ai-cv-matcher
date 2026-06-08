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
│   ├── logger/
│   │   ├── __init__.py         # API pública: get_logger, setup_logging, LogContext
│   │   ├── config.py           # LoggingConfig (desde variables de entorno)
│   │   ├── context.py          # LogContext — correlation ID con contextvars
│   │   ├── filters.py          # SensitiveDataFilter, ContextFilter
│   │   ├── formatters.py       # DevFormatter (coloreado), JSONFormatter
│   │   └── core.py             # Configuración del logger raíz
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

# 4. Instalar el proyecto en modo editable (registra src/ como raíz de paquetes)
uv pip install -e .

# 5. Configurar variables de entorno
cp .env.example .env
# Abrir .env y completar con tus API keys

# 6. Activar protección contra secretos expuestos
uv tool install pre-commit
pre-commit install
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

# 4. Instalar el proyecto en modo editable (registra src/ como raíz de paquetes)
pip install -e .

# 5. Configurar variables de entorno
cp .env.example .env
# Abrir .env y completar con tus API keys

# 6. Activar protección contra secretos expuestos
pip install pre-commit
pre-commit install
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

## Seguridad — Prevención de secretos expuestos

Este proyecto usa [gitleaks](https://github.com/gitleaks/gitleaks) a través del framework [pre-commit](https://pre-commit.com/) para bloquear automáticamente cualquier commit que contenga API keys u otros secretos antes de que entren al historial de git. Ver [docs/seguridad.md](docs/seguridad.md) para la documentación completa, incluyendo qué hacer si una clave queda expuesta.

### Activar la protección (obligatorio al clonar)

```bash
# 1. Instalar pre-commit
pip install pre-commit
# o con uv:
uv tool install pre-commit

# 2. Registrar el hook en tu clon local (solo una vez)
pre-commit install
```

A partir de ese momento, cada `git commit` ejecuta gitleaks automáticamente. Si detecta un secreto, **el commit se cancela** y muestra qué archivo y línea contiene el problema.

### Qué detecta

| Tipo de secreto | Ejemplo de patrón |
|---|---|
| Google API Key | `AIza[A-Za-z0-9_-]{35}` |
| OpenAI API Key | `sk-[A-Za-z0-9]{20,}` |
| OpenAI Project Key | `sk-proj-[A-Za-z0-9_-]{20,}` |
| AWS Access Key | `AKIA[0-9A-Z]{16}` |
| GitHub PAT | `gh[pousr]_[A-Za-z0-9]{36,}` |
| Slack Bot Token | `xoxb-[0-9]+-[A-Za-z0-9]+` |
| + todas las reglas por defecto de gitleaks | |

### Archivos de configuración

| Archivo | Propósito |
|---|---|
| [.pre-commit-config.yaml](.pre-commit-config.yaml) | Define qué hooks se ejecutan y con qué versión de gitleaks |
| [.gitleaks.toml](.gitleaks.toml) | Reglas adicionales y exclusiones (placeholders, rutas ignoradas) |

### Flujo normal de trabajo

```
git add mis_cambios.py
git commit -m "feat: nueva funcionalidad"
  └─ pre-commit ejecuta gitleaks
       ├─ Sin secretos → commit pasa normalmente
       └─ Con secreto  → commit cancelado, se muestra la ubicación del problema
```

### Si gitleaks bloquea un falso positivo

Si un valor detectado **no es un secreto real** (por ejemplo, un ID de prueba con formato similar a una key), tienes dos opciones:

**Opción 1 — Agregar una excepción en `.gitleaks.toml`** (recomendado para patrones recurrentes):
```toml
[allowlist]
regexes = ["tu-patron-especifico"]
```

**Opción 2 — Marcar la línea puntual** con un comentario inline:
```python
TEST_ID = "AIzaFAKEVALUEFORTESTING12345678901"  # gitleaks:allow
```

### Ejecutar el escaneo manualmente

```bash
# Escanear solo los archivos staged (igual que el hook)
pre-commit run gitleaks

# Escanear todos los archivos del repo
pre-commit run gitleaks --all-files

# Escanear el historial completo de commits
gitleaks detect --config .gitleaks.toml
```

> Las API keys **nunca** deben estar en el código. Siempre en `.env` (ya incluido en `.gitignore`). Ver `.env.example` para la plantilla.

## Logging

El módulo `src/logger/` centraliza toda la configuración de logs. Todos los loggers del proyecto viven bajo la jerarquía `ai-cv-matcher.*` y se configuran una única vez al arrancar la aplicación.

### Variables de entorno

| Variable | Valores | Por defecto | Descripción |
|---|---|---|---|
| `LOG_LEVEL` | `DEBUG` `INFO` `WARNING` `ERROR` `CRITICAL` | `INFO` | Nivel mínimo de emisión |
| `LOG_FORMAT` | `text` `json` | `text` | Formato de salida en consola |
| `LOG_FILE_ENABLED` | `true` `false` | `false` | Activa el handler de archivo con rotación |
| `LOG_FILE_PATH` | ruta | `logs/app.log` | Ubicación del archivo de log |
| `LOG_FILE_MAX_MB` | entero | `10` | Tamaño máximo por archivo en MB |
| `LOG_FILE_BACKUP_COUNT` | entero | `5` | Número de archivos rotados a conservar |
| `APP_NAME` | texto | `ai-cv-matcher` | Prefijo del namespace de todos los loggers |
| `APP_ENV` | `development` `staging` `production` | `development` | `production` fuerza `LOG_FORMAT=json` |

> Configura estas variables en tu `.env`. Ver `.env.example` para la plantilla completa.

### Usar el logger en un módulo

```python
from logger import get_logger

logger = get_logger(__name__)

logger.info("Procesando archivo", extra={"archivo": "cv_demo.pdf"})
logger.warning("python-docx no instalado")
logger.exception("Fallo en llamada LLM")
```

`get_logger` acepta `__name__`, un nombre corto (`"tools.cv_parser"`) o el nombre completo con prefijo (`"ai-cv-matcher.tools.cv_parser"`). Todos son equivalentes.

### Correlacionar una operación completa

`LogContext` inyecta un ID corto en todos los logs producidos dentro del bloque, sin necesidad de pasarlo manualmente:

```python
from logger import get_logger, LogContext

logger = get_logger(__name__)

with LogContext("parse_cv") as cid:
    logger.info("Iniciando procesamiento")   # [a1b2c3d4] | ...
    cv = cv_parser.parsear_archivo_cv(ruta)  # todos los logs internos llevan el mismo cid
    logger.info("CV procesado correctamente")
```

### Formato de salida

**Desarrollo (`LOG_FORMAT=text`)**

```
2026-04-28 15:30:01 | INFO     | [a1b2c3d4] | ai-cv-matcher.clients.llm | LLMClient inicializado | Proveedor: openai | Modelo: gpt-4o-mini | Temp: 0.0
2026-04-28 15:30:03 | INFO     | [a1b2c3d4] | ai-cv-matcher.tools.cv_parser | CV procesado correctamente
```

**Producción (`LOG_FORMAT=json` o `APP_ENV=production`)**

```json
{"timestamp": "2026-04-28T15:30:01+00:00", "level": "INFO", "logger": "ai-cv-matcher.clients.llm", "message": "LLMClient inicializado | Proveedor: openai | Modelo: gpt-4o-mini | Temp: 0.0", "correlation_id": "a1b2c3d4", "module": "client_llm", "function": "__init__", "line": 73}
```

### Seguridad

`SensitiveDataFilter` redacta automáticamente cualquier API key o bearer token que aparezca en un mensaje de log antes de emitirlo:

```
# Lo que se escribe:
logger.info(f"Usando key: {api_key}")

# Lo que se emite:
INFO | Usando key: [OPENAI_KEY_REDACTED]
```

Los dumps completos de objetos Pydantic (útiles en depuración) se emiten en nivel `DEBUG` y permanecen silenciosos con la configuración por defecto (`LOG_LEVEL=INFO`).

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
from tools.cv_anonymizer import CVAnonymizer
from tools.cv_parser import CVParser
from tools.jd_parser import JDParser

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

## Hoja de ruta

- [ ] Módulo 02: Indexación vectorial con Qdrant
- [ ] Matching CV vs JD con scoring cuantitativo
- [ ] API REST con FastAPI
- [ ] NER avanzado para detección de nombres (reemplazar heurística actual)
- [ ] Soporte para múltiples idiomas y mercados laborales

---

## Referencia de comandos Git

Comandos utilizados para configurar y publicar este repositorio desde cero.

### Crear y configurar el repositorio

```bash
# Inicializar un repositorio local (uv lo hace automáticamente con `uv init`)
git init

# Crear el repositorio remoto privado en GitHub (requiere GitHub CLI)
gh repo create ai-cv-matcher --private --description "descripción del proyecto"

# Vincular el repositorio local con el remoto
git remote add origin https://github.com/<usuario>/ai-cv-matcher.git
```

### Preparar y hacer el primer commit

```bash
# Ver el estado actual del repositorio (archivos modificados, staged, untracked)
git status

# Agregar archivos específicos al área de staging
git add archivo.py carpeta/

# Agregar todos los archivos (respetando .gitignore)
git add .

# Quitar un archivo del staging sin borrarlo del disco
git rm --cached archivo.py

# Crear un commit con mensaje descriptivo
git commit -m "feat: descripción del cambio"

# Renombrar la rama actual a 'main'
git branch -M main

# Subir la rama main al remoto por primera vez y configurar el upstream
git push -u origin main
```

### Trabajar con ramas

```bash
# Ver todas las ramas (locales y remotas)
git branch -a

# Crear una nueva rama
git branch develop

# Cambiar a una rama existente
git checkout develop

# Crear y cambiar a una nueva rama en un solo paso
git checkout -b feature/nueva-funcionalidad

# Subir una rama local al remoto por primera vez
git push --set-upstream origin develop

# Subir cambios en una rama que ya tiene upstream configurado
git push
```

### Sincronizar ramas

```bash
# Traer los últimos cambios del remoto sin fusionar
git fetch origin

# Traer y fusionar los cambios del remoto en la rama actual
git pull origin main

# Fusionar otra rama en la rama actual (ej: traer main a develop)
git checkout develop
git merge main

# Ver el historial de commits en una línea por commit
git log --oneline
```

### Flujo de trabajo usado en este proyecto

```bash
# 1. Crear el repo privado en GitHub
gh repo create ai-cv-matcher --private

# 2. Agregar archivos y hacer el commit inicial
git add .
git commit -m "feat: initial commit"

# 3. Renombrar rama a main, vincular remoto y hacer push
git branch -M main
git remote add origin https://github.com/DevForAll/ai-cv-matcher.git
git push -u origin main

# 4. Crear rama develop localmente (ya existía) y publicarla
git checkout develop
git merge main          # asegurar que develop tiene los últimos cambios de main
git push --set-upstream origin develop
```
