"""
Cliente LLM unificado — Versión optimizada y escalable.
Permite interactuar con OpenAI y Google Gemini de forma estandarizada,
soportando salidas estructuradas (Pydantic) y texto plano.
"""

import os
import time
import logging
from enum import Enum
from typing import Optional, TypeVar, Type, Union, overload, Any
from pydantic import BaseModel
import tiktoken

# Tipado genérico para modelos Pydantic
T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger("shared.llm-client")

class Proveedor(str, Enum):
    """Enumeración de proveedores soportados."""
    OPENAI = "openai"
    GEMINI = "gemini"

class LLMClientError(Exception):
    """Excepción base para errores del cliente LLM."""
    pass

class LLMClient:
    """
    Cliente unificado para múltiples proveedores de LLM.

    Proporciona una interfaz común para realizar llamadas a modelos de lenguaje,
    gestionando automáticamente reintentos, conteo de tokens, y validación
    de esquemas de salida.
    """

    def __init__(
            self,
            proveedor: Proveedor = Proveedor.OPENAI,
            modelo: str = "gpt-4o-mini",
            temperatura: float = 0.0,
            max_tokens: int = 1500,
            max_reintentos: int = 3,
            api_key: Optional[str] = None
    ):
        """
        Inicializa el cliente con la configuración deseada.

        Args:
            proveedor (Proveedor): El proveedor de IA a utilizar.
            modelo (str): Identificador del modelo (ej: 'gpt-4o-mini', 'gemini-1.5-flash').
            temperatura (float): Creatividad de la respuesta (0.0 a 1.0).
            max_tokens (int): Límite de tokens en la respuesta.
            max_reintentos (int): Número de intentos en caso de errores temporales.
            api_key (Optional[str]): Llave de API. Si no se provee, se busca en env vars.
        """
        self.proveedor = proveedor
        self.modelo = modelo
        self.temperatura = temperatura
        self.max_tokens = max_tokens
        self.max_reintentos = max_reintentos

        # Inicializar el cliente específico según el proveedor
        self._cliente = self._init_cliente(api_key)

        # Tokenizer (usamos cl100k_base como estándar de facto para estimaciones)
        try:
            self._encoding = tiktoken.encoding_for_model("gpt-4o")
        except Exception:
            self._encoding = tiktoken.get_encoding("cl100k_base")

        logger.info(
            f"LLMClient inicializado | Proveedor: {proveedor.value} | "
            f"Modelo: {modelo} | Temp: {temperatura}"
        )

    def _init_cliente(self, api_key: Optional[str]) -> Any:
        """Configura e instancia el SDK del proveedor seleccionado."""
        if self.proveedor == Proveedor.OPENAI:
            from openai import OpenAI
            key = api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                raise LLMClientError("OPENAI_API_KEY no encontrada. Configúrala en el archivo .env")
            return OpenAI(api_key=key)

        elif self.proveedor == Proveedor.GEMINI:
            import google.generativeai as genai
            key = api_key or os.getenv("GOOGLE_API_KEY")
            if not key:
                raise LLMClientError("GOOGLE_API_KEY no encontrada. Configúrala en el archivo .env")
            genai.configure(api_key=key)
            return genai.GenerativeModel(self.modelo)

        raise LLMClientError(f"Proveedor no soportado: {self.proveedor}")

    def contar_tokens(self, texto: str) -> int:
        """Estima la cantidad de tokens en un texto."""
        return len(self._encoding.encode(texto))


    @overload
    def llamar(self, system_prompt: str, user_message: str, schema: Type[T]) -> T:
        """Firma para cuando se solicita salida estructurada."""
        ...

    @overload
    def llamar(self, system_prompt: str, user_message: str, schema: None = None) -> str:
        """Firma para cuando se solicita salida de texto plano."""
        ...

    def llamar(
            self,
            system_prompt: str,
            user_message: str,
            schema: Optional[Type[T]] = None
    ) -> str | None | Any:
        """
        Ejecuta una llamada al LLM con lógica de reintento y validación.

        Args:
            system_prompt (str): Instrucciones de comportamiento para el modelo.
            user_message (str): Consulta o datos del usuario.
            schema (Optional[Type[BaseModel]]): Clase Pydantic para estructurar la respuesta.

        Returns:
            Union[BaseModel, str]: Instancia del esquema si se proveyó, o string de texto.
        """
        tokens_in = self.contar_tokens(system_prompt + user_message)
        logger.info(f"Llamada LLM | Tokens Estimados: {tokens_in}")

        for intento in range(1, self.max_reintentos + 1):
            try:
                inicio = time.time()

                if self.proveedor == Proveedor.OPENAI:
                    resultado = self._ejecutar_openai(system_prompt, user_message, schema)
                else:
                    resultado = self._ejecutar_gemini(system_prompt, user_message, schema)

                duracion = round(time.time() - inicio, 2)
                logger.info(f"Éxito | Intento: {intento} | Duración: {duracion}s")

                # Log de depuración para salidas estructuradas
                if schema:
                    logger.info(f"--- [DEBUG] Datos Extraídos ({schema.__name__}) ---")
                    logger.info(f"\n{resultado.model_dump_json(indent=2, ensure_ascii=False)}")
                    logger.info("-" * 50)

                return resultado

            except Exception as e:
                if self._es_error_fatal(e):
                    self._manejar_error_fatal(e)

                if intento == self.max_reintentos:
                    logger.error(f"Error final tras {intento} intentos: {str(e)}")
                    raise LLMClientError(f"Fallo crítico en LLM: {str(e)}") from e

                tiempo_espera = 2 ** intento
                logger.warning(f"Error temporal ({type(e).__name__}): {e}. Reintentando en {tiempo_espera}s...")
                time.sleep(tiempo_espera)
        return None

    def _ejecutar_openai(self, system: str, user: str, schema: Optional[Type[T]]) -> Union[T, str]:
        """Lógica interna para OpenAI."""
        mensajes = [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]

        if schema:
            completion = self._cliente.beta.chat.completions.parse(
                model=self.modelo,
                messages=mensajes,
                temperature=self.temperatura,
                max_tokens=self.max_tokens,
                response_format=schema,
            )
            return completion.choices[0].message.parsed

        completion = self._cliente.chat.completions.create(
            model=self.modelo,
            messages=mensajes,
            temperature=self.temperatura,
            max_tokens=self.max_tokens,
        )
        return completion.choices[0].message.content

    def _ejecutar_gemini(self, system: str, user: str, schema: Optional[Type[T]]) -> Union[T, str]:
        """Lógica interna para Google Gemini."""
        import google.generativeai as genai
        import json

        prompt = f"{system}\n\n{user}"

        config_params: dict[str, Any] = {
            "temperature": self.temperatura,
            "max_output_tokens": self.max_tokens,
        }

        if schema:
            config_params["response_mime_type"] = "application/json"
            config_params["response_schema"] = schema.model_json_schema()

        response = self._cliente.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(**config_params)
        )

        if schema:
            try:
                datos = json.loads(response.text)
                return schema(**datos)
            except Exception as e:
                raise LLMClientError(f"Error al parsear JSON de Gemini: {str(e)}")

        return response.text

    @staticmethod
    def _es_error_fatal(e: Exception) -> bool:
        """Identifica errores que no vale la pena reintentar."""
        from openai import BadRequestError
        if isinstance(e, (BadRequestError, ValueError, TypeError)):
            return True
        if "api_key" in str(e).lower() or "authentication" in str(e).lower():
            return True
        return False

    @staticmethod
    def _manejar_error_fatal(e: Exception):
        """Procesa errores fatales antes de lanzarlos."""
        from openai import BadRequestError
        if isinstance(e, BadRequestError) and "response_format" in str(e).lower():
            logger.error("Esquema Pydantic incompatible con Structured Outputs de OpenAI.")
        raise e
