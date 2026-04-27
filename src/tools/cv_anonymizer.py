import re

# ============================================================
# SECCIÓN 2: Anonimizador de CVs
# ============================================================

class CVAnonymizer:
    """
    Clase encargada de la desidentificación de datos sensibles en documentos de CV.

    Su función es localizar y reemplazar Información de Identificación Personal (PII)
    como DNI, números de teléfono, correos electrónicos y nombres propios por etiquetas
    genéricas. Esto garantiza el cumplimiento de leyes de protección de datos (como la
    Ley 29733 en Perú) y reduce el sesgo algorítmico durante el proceso de selección.

    # Conceptos clave:
    # ----------------
    # PII (Personally Identifiable Information): Datos que permiten identificar a una persona.
    # NER (Named Entity Recognition): Técnica para identificar entidades como nombres en texto.
    # HEURÍSTICA: Es una regla práctica o "atajo" lógico que suele funcionar bien en la
    #             mayoría de los casos, aunque no garantiza el 100% de precisión.
    """

    # Patrones para PII peruana usando expresiones regulares (Regex)
    # La librería 're' se utiliza para compilar estos patrones (re.compile)
    # para que las búsquedas sean mucho más rápidas y eficientes en textos largos.

    # PATRON_DNI: Busca exactamente 8 dígitos (\d{8}) entre límites de palabra (\b)
    PATRON_DNI = re.compile(r"\b\d{8}\b")

    # PATRON_RUC: Busca exactamente 11 dígitos (\d{11}) entre límites de palabra (\b)
    PATRON_RUC = re.compile(r"\b\d{11}\b")

    # PATRON_TELEFONO: Busca números celulares (9 + 8 dígitos) o fijos (7 u 8 dígitos).
    # Opcionalmente captura el prefijo de país (+51).
    PATRON_TELEFONO = re.compile(r"\b(?:\+51\s?)?(?:9\d{8}|\d{7,8})\b")

    # PATRON_EMAIL: Identifica el formato estándar de un correo electrónico:
    # usuario@dominio.tld con caracteres comunes (letras, números, puntos, etc.).
    PATRON_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")

    # Lista simple de nombres peruanos comunes (en producción usar NER)
    INDICADORES_NOMBRE = ["nombres:", "nombre:", "apellidos:", "apellido:"]

    def anonimizar_texto(self, texto: str) -> str:
        """
        Detecta y ofusca datos personales en una cadena de texto.

        Este metodo aplica una serie de sustituciones basadas en expresiones regulares
        para reemplazar correos, teléfonos, DNI y RUC por etiquetas informativas
        (ej: [DNI_REDACTADO]). También aplica una HEURÍSTICA (una regla práctica basada
        en la estructura común de los CVs) para detectar y anonimizar el nombre del
        candidato si aparece al inicio del documento.

        Args:
            texto (str): El contenido textual original del CV.

        Returns:
            str: El texto anonimizado listo para ser procesado por un LLM o almacenado.
        """
        texto = self.PATRON_EMAIL.sub("[EMAIL_REDACTADO]", texto)
        texto = self.PATRON_DNI.sub("[DNI_REDACTADO]", texto)
        texto = self.PATRON_RUC.sub("[RUC_REDACTADO]", texto)
        texto = self.PATRON_TELEFONO.sub("[TELEFONO_REDACTADO]", texto)

        # Eliminar la primera línea si parece ser el nombre del candidato
        lineas = texto.split("\n")
        if lineas and len(lineas[0].split()) <= 5:
            # Primera línea corta, probablemente es el nombre
            lineas[0] = "[NOMBRE_REDACTADO]"

        return "\n".join(lineas)