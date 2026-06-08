# Política de seguridad

## Protecciones activas

Este proyecto utiliza `pre-commit` + `gitleaks` para prevenir la exposición accidental de API keys u otros secretos en el historial de git. Ver [docs/seguridad.md](docs/seguridad.md) para la documentación técnica completa.

## Reportar una vulnerabilidad

Si encuentras una vulnerabilidad de seguridad en este proyecto, por favor **no abras un issue público**. En su lugar:

1. Envía un email a **jhonlt40@gmail.com** con el asunto `[SECURITY] ai-cv-matcher`.
2. Describe el problema, los pasos para reproducirlo y el impacto potencial.
3. Recibirás respuesta en un plazo máximo de 72 horas.

## Si encuentras una clave expuesta

Si encuentras credenciales reales en el código o historial del repo:

1. Notifica al equipo por email antes de divulgarlo públicamente.
2. No uses ni compartas las credenciales encontradas.
3. Sigue los pasos de [docs/seguridad.md — Qué hacer si una clave queda expuesta](docs/seguridad.md#qué-hacer-si-una-clave-queda-expuesta).

## Alcance

Este proyecto maneja exclusivamente datos de CVs y descripciones de puestos. No almacena contraseñas de usuarios ni información financiera. Los CVs son anonimizados antes de cualquier procesamiento (ver [política de privacidad](README.md#privacidad)).
