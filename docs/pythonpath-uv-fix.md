# Diagnóstico: `ModuleNotFoundError: No module named 'tools'` con `uv run`

## Resumen ejecutivo

El error ocurre porque **el IDE (PyCharm) manipula `sys.path` en tiempo de ejecución** de forma invisible,
mientras que `uv run` ejecuta Python en condiciones "limpias" sin ese ajuste.
Son el mismo intérprete, el mismo código, pero con rutas de búsqueda de módulos distintas.

---

## 1. Por qué funciona en el IDE

PyCharm almacena la configuración del proyecto en `.idea/ai-cv-matcher.iml`:

```xml
<content url="file://$MODULE_DIR$">
  <sourceFolder url="file://$MODULE_DIR$/src" isTestSource="false" />
</content>
```

La línea `<sourceFolder ... />` le indica a PyCharm que `src/` es una **Sources Root** (raíz de fuentes).
Cuando lanzas el script con el botón **RUN**, PyCharm antepone automáticamente
la ruta absoluta de `src/` a la variable de entorno `PYTHONPATH` antes de invocar Python.

Python construye `sys.path` a partir de `PYTHONPATH`, por lo que al momento de ejecutar
`from tools.cv_parser import CVParser`, el intérprete busca el paquete `tools` en:

```
C:\workspace\REPOSITORIES\ai-cv-matcher\src\   ← añadido por PyCharm
C:\workspace\REPOSITORIES\ai-cv-matcher\src\rag\  ← directorio del script
...
```

`src\tools\` existe → importación exitosa.

---

## 2. Por qué falla con `uv run`

```bash
uv run python .\src\rag\pipeline.py
```

`uv run` ejecuta Python sin ningún `PYTHONPATH` especial.
Python, por su parte, solo añade a `sys.path` el **directorio del script que se está ejecutando**
(`src\rag\`) y los paquetes instalados en el entorno virtual.

En ese momento `sys.path` contiene:

```
C:\workspace\REPOSITORIES\ai-cv-matcher\src\rag\   ← directorio del script
C:\workspace\REPOSITORIES\ai-cv-matcher\.venv\Lib\site-packages\
...
```

`src\tools\` no está en ninguna de esas rutas → `ModuleNotFoundError`.

### Diagrama comparativo

```
                    sys.path en ejecución
                    ┌─────────────────────────────────────────────┐
  PyCharm RUN  →   │ src/          ← Sources Root (PyCharm añade) │  ✅ tools encontrado
                    │ src/rag/      ← directorio del script        │
                    └─────────────────────────────────────────────┘

                    ┌─────────────────────────────────────────────┐
  uv run       →   │ src/rag/      ← directorio del script        │  ❌ tools NO encontrado
                    │ .venv/...     ← site-packages               │
                    └─────────────────────────────────────────────┘
```

---

## 3. Solución aplicada: instalación en modo editable

Se declaró el layout `src/` en `pyproject.toml` y se instaló el proyecto en modo editable.

```toml
[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```

```bash
uv pip install -e .
```

Esto crea un enlace en `.venv/Lib/site-packages/` que apunta a `src/`,
por lo que todos los paquetes bajo `src/` (`tools`, `rag`, `clients`, `logger`, etc.)
quedan disponibles como módulos de primer nivel en cualquier contexto de ejecución.

**Resultado:** `uv run python src/rag/pipeline.py` funciona sin variables de entorno adicionales.

---

## 4. Convención de imports en este proyecto

Nunca usar el prefijo `src.` en los imports:

```python
# Correcto
from tools.cv_parser import CVParser
from logger import get_logger

# Incorrecto — acopla el código a la estructura de directorios
from src.tools.cv_parser import CVParser
```

El prefijo `src.` rompería la compatibilidad si el proyecto se empaqueta como librería
o si se renombra el directorio.
