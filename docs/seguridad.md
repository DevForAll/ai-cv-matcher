# Seguridad — Gestión de secretos

## Protecciones activas

El proyecto tiene dos capas de protección contra la exposición accidental de API keys u otros secretos:

### 1. `.gitignore` — evita que `.env` entre al repo

El archivo `.env` (donde viven las claves reales) está en `.gitignore` y nunca será trackeado por git. Solo se versiona `.env.example`, que contiene exclusivamente placeholders vacíos.

### 2. `pre-commit` + `gitleaks` — bloquea el commit si detecta un secreto

Antes de que cualquier commit entre al historial, `gitleaks` escanea los archivos staged. Si detecta un patrón de API key real, el commit se cancela y muestra exactamente dónde está el problema.

**Archivos de configuración:**

| Archivo | Propósito |
|---|---|
| [.pre-commit-config.yaml](../.pre-commit-config.yaml) | Define que se use gitleaks v8.21.2 en cada commit |
| [.gitleaks.toml](../.gitleaks.toml) | Reglas adicionales y exclusiones (placeholders, paths ignorados) |

**Patrones que detecta gitleaks en este proyecto:**

| Tipo | Patrón |
|---|---|
| Google API Key | `AIza[A-Za-z0-9_-]{35}` |
| OpenAI API Key | `sk-[A-Za-z0-9]{20,}` |
| OpenAI Project Key | `sk-proj-[A-Za-z0-9_-]{20,}` |
| AWS Access Key | `AKIA[0-9A-Z]{16}` |
| GitHub PAT | `gh[pousr]_[A-Za-z0-9]{36,}` |
| Slack Bot Token | `xoxb-[0-9]+-[A-Za-z0-9]+` |
| Reglas por defecto de gitleaks | (incluidas via `useDefault = true`) |

---

## Activar la protección al clonar

El hook de `pre-commit` no se activa solo — requiere un comando manual tras clonar:

```bash
# Con uv
uv tool install pre-commit
pre-commit install

# Con pip
pip install pre-commit
pre-commit install
```

Sin este paso, los commits no serán escaneados en esa máquina.

---

## Comandos de escaneo manual

```bash
# Escanear solo los archivos staged (igual que el hook automático)
pre-commit run gitleaks

# Escanear todos los archivos del repo
pre-commit run gitleaks --all-files

# Escanear el historial completo de commits
gitleaks detect --config .gitleaks.toml

# Escanear el historial y generar reporte JSON
gitleaks detect --config .gitleaks.toml --report-path reporte-secretos.json
```

---

## Qué hacer si una clave queda expuesta

Si a pesar de las protecciones una clave llega a un repo público, el orden de acciones es:

### 1. Revocar la clave (prioridad máxima — hacerlo antes que cualquier otra cosa)

Una clave revocada es inútil aunque alguien la haya copiado. Esto corta el riesgo de inmediato.

| Proveedor | Dónde revocar |
|---|---|
| Google AI / Gemini | https://aistudio.google.com/app/apikey |
| Google Cloud | https://console.cloud.google.com/apis/credentials |
| OpenAI | https://platform.openai.com/api-keys |
| AWS | https://console.aws.amazon.com/iam/home#/security_credentials |
| GitHub | https://github.com/settings/tokens |

### 2. Poner el repo en privado temporalmente

Mientras se limpia el historial, reducir la exposición poniendo el repo en privado en GitHub → Settings → Danger Zone → Change visibility.

### 3. Limpiar el historial con `git filter-repo`

```bash
# Instalar si no está disponible
uv tool install git-filter-repo

# Crear archivo de reemplazos
echo 'LA_CLAVE_EXPUESTA==>CLAVE_ELIMINADA' > replacements.txt

# Reescribir todo el historial
git filter-repo --replace-text replacements.txt --force

# Restaurar el remote (git filter-repo lo elimina)
git remote add origin https://github.com/DevForAll/ai-cv-matcher.git

# Subir el historial limpio
git push origin --force --all
```

### 4. Solicitar purga de caché a GitHub

Tras el force push, GitHub puede seguir sirviendo los commits viejos en caché. Abrir un ticket en https://support.github.com solicitando la purga del repo afectado.

### 5. Resolver la alerta en GitGuardian

Si GitGuardian detectó la clave, entrar a https://dashboard.gitguardian.com y marcar el incidente como **Revoked** o **Resolved**.

---

## Reglas para el código

- Las claves siempre se leen desde variables de entorno: `os.getenv("NOMBRE_KEY")`
- Nunca pasar una clave como argumento por defecto en una función: `def func(key="AIza...")`
- Si una prueba necesita una clave, usar una variable de entorno o un mock — nunca un valor real hardcodeado
- El archivo `.env.example` solo puede contener placeholders vacíos o descriptivos (`=` o `=sk-...`)

---

## Falsos positivos

Si gitleaks bloquea un valor que no es un secreto real (por ejemplo, un ID de prueba con formato similar a una key), hay dos formas de excluirlo:

**Opción 1 — Exclusión global en `.gitleaks.toml`** (para patrones recurrentes):
```toml
[allowlist]
regexes = ["patron-especifico-a-ignorar"]
```

**Opción 2 — Excepción inline** (para una línea puntual):
```python
TEST_MOCK_ID = "AIzaFAKEVALUEFORTESTING12345678901"  # gitleaks:allow
```
