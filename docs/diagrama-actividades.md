# Diagrama de Actividades — AI CV Matcher

Muestra el flujo de actividades para procesar un CV y una Job Description, desde la lectura del archivo hasta el objeto estructurado de salida.

---

## Flujo de procesamiento de CV

```mermaid
flowchart TD
    CV_START([Inicio — parsear_archivo_cv]) --> CV_READ[Leer ruta del archivo]
    CV_READ --> CV_FMT{¿Formato?}

    CV_FMT -->|.pdf| CV_PDF[PyMuPDF\nextrae texto página a página]
    CV_FMT -->|.docx / .doc| CV_DOCX[python-docx\nextrae párrafos]
    CV_FMT -->|.txt u otro| CV_TXT[read_text UTF-8]

    CV_PDF & CV_DOCX & CV_TXT --> ANON_START

    subgraph ANON["CVAnonymizer — anonimizar_texto"]
        ANON_START[Texto crudo] --> R1[Redactar emails\nPATRON_EMAIL]
        R1 --> R2[Redactar DNI\n8 dígitos exactos]
        R2 --> R3[Redactar RUC\n11 dígitos exactos]
        R3 --> R4[Redactar teléfono\nformato peruano con o sin +51]
        R4 --> R5{¿Primera línea ≤ 5 palabras?}
        R5 -->|Sí — probable nombre| R6[Reemplazar por NOMBRE_REDACTADO]
        R5 -->|No| R7[Conservar línea]
        R6 & R7 --> ANON_OUT[Texto anonimizado]
    end

    ANON_OUT --> CV_PROMPT[Construir system prompt + user message\ntruncado a 3 000 caracteres]
    CV_PROMPT --> LLM_CV[LLMClient.llamar\nschema=CVEstructurado]

    subgraph LLM_CALL_CV["LLMClient — llamada con reintentos"]
        LLM_CV --> PROV_CV{¿Proveedor?}
        PROV_CV -->|OpenAI| OAI_CV[beta.completions.parse\nStructured Outputs]
        PROV_CV -->|Gemini| GEM_CV[GenerativeModel\nresponse_mime_type JSON]
        OAI_CV & GEM_CV --> OK_CV{¿Éxito?}
        OK_CV -->|Sí| VAL_CV[Validar con Pydantic\nCVEstructurado]
        OK_CV -->|Error fatal\nBadRequest · auth| ERR_CV[Lanzar LLMClientError]
        OK_CV -->|Error temporal\ntimeout · rate limit| WAIT_CV[Esperar 2ⁿ segundos\nbackoff exponencial]
        WAIT_CV --> RETRY_CV{¿Intentos < 3?}
        RETRY_CV -->|Sí| PROV_CV
        RETRY_CV -->|No| ERR_CV
    end

    VAL_CV --> LOG_CV[logger.debug — dump JSON del objeto]
    LOG_CV --> CV_END([CVEstructurado devuelto])
```

---

## Flujo de procesamiento de Job Description

```mermaid
flowchart TD
    JD_START([Inicio — parsear_archivo_jd]) --> JD_TITLE[Inferir título desde nombre de archivo\nsi no se proporciona]
    JD_TITLE --> JD_READ[Leer ruta del archivo]
    JD_READ --> JD_FMT{¿Formato?}

    JD_FMT -->|.pdf| JD_PDF[PyMuPDF\nextrae texto página a página]
    JD_FMT -->|.docx / .doc| JD_DOCX[python-docx\nextrae párrafos]
    JD_FMT -->|.txt u otro| JD_TXT[read_text UTF-8]

    JD_PDF & JD_DOCX & JD_TXT --> JD_PROMPT

    JD_PROMPT[Construir system prompt + user message\ntruncado a 4 000 caracteres] --> LLM_JD[LLMClient.llamar\nschema=JobDescription]

    subgraph LLM_CALL_JD["LLMClient — llamada con reintentos"]
        LLM_JD --> PROV_JD{¿Proveedor?}
        PROV_JD -->|OpenAI| OAI_JD[beta.completions.parse\nStructured Outputs]
        PROV_JD -->|Gemini| GEM_JD[GenerativeModel\nresponse_mime_type JSON]
        OAI_JD & GEM_JD --> OK_JD{¿Éxito?}
        OK_JD -->|Sí| VAL_JD[Validar con Pydantic\nJobDescription]
        OK_JD -->|Error fatal| ERR_JD[Lanzar LLMClientError]
        OK_JD -->|Error temporal| WAIT_JD[Esperar 2ⁿ segundos\nbackoff exponencial]
        WAIT_JD --> RETRY_JD{¿Intentos < 3?}
        RETRY_JD -->|Sí| PROV_JD
        RETRY_JD -->|No| ERR_JD
    end

    VAL_JD --> TITLE_CHECK{¿Título extraído\nes válido?}
    TITLE_CHECK -->|No| TITLE_FIX[Usar título proporcionado como fallback]
    TITLE_CHECK -->|Sí| LOG_JD
    TITLE_FIX --> LOG_JD

    LOG_JD[logger.debug — dump JSON del objeto] --> JD_END([JobDescription devuelta])
```

---

## Logger — actividades transversales

El módulo `logger` actúa de forma transversal en ambos flujos. No interrumpe las actividades sino que las envuelve.

```mermaid
flowchart LR
    subgraph LC["LogContext — bloque de operación"]
        direction TB
        INIT[Generar correlation ID\nuuid4 primeros 8 hex] --> CTX[Inyectar ID en ContextVar]
        CTX --> OP[Actividades del flujo\nCV o JD]
        OP --> RESET[Restaurar ContextVar al salir]
    end

    subgraph EMIT["Emisión de cada log record"]
        direction TB
        MSG[logger.info / debug / warning / exception] --> CF[ContextFilter\nañade correlation_id al record]
        CF --> SF[SensitiveDataFilter\nredacta API keys y bearer tokens]
        SF --> FMT{¿Entorno?}
        FMT -->|development| DEV[DevFormatter\ncoloreado con timestamp]
        FMT -->|production| JSON[JSONFormatter\nuna línea JSON por evento]
        DEV & JSON --> OUT[Consola / Archivo rotativo]
    end

    LC --> EMIT
```
