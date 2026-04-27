from pydantic import BaseModel, Field
from typing import Literal

# ============================================================
# SECCIÓN 1: Schemas Pydantic para CV Matcher
# ============================================================

class Idioma(BaseModel):
    """Representa el dominio de un idioma por parte del candidato."""
    idioma: str = Field(description="Nombre del idioma (ej: Inglés, Francés)")
    nivel: str = Field(description="Nivel alcanzado (ej: B2, Nativo, Avanzado)")


class CVEstructurado(BaseModel):
    """
    Representa la información profesional extraída y estructurada de un Curriculum Vitae.

    Su función principal es servir como un contenedor de datos limpio y tipado que facilita
    el procesamiento posterior, como la indexación en bases de datos vectoriales (RAG)
    o el emparejamiento con ofertas laborales, eliminando cualquier dato de carácter
    personal para cumplir con normativas de privacidad.

    NOTA CRÍTICA DE PRIVACIDAD:
    Los campos 'nombre', 'dni', 'telefono', 'email' y 'direccion'
    NO se almacenan aquí. Solo se guardan datos profesionales.
    El ID de candidato es un UUID interno.
    """
    candidato_id: str = Field(
        description="UUID interno del candidato (sin relación al documento original)"
    )
    nivel_experiencia: Literal["junior", "semi-senior", "senior", "lead"] = Field(
        description="Nivel inferido del total de años de experiencia"
    )
    anos_experiencia: float = Field(
        ge=0,
        description="Total de años de experiencia profesional estimados"
    )
    skills_tecnicos: list[str] = Field(
        description="Lista de tecnologías, herramientas y habilidades técnicas"
    )
    skills_blandos: list[str] = Field(
        description="Habilidades interpersonales y de gestión mencionadas"
    )
    industrias: list[str] = Field(
        description="Sectores donde ha trabajado (banca, retail, minería, etc.)"
    )
    cargos_anteriores: list[str] = Field(
        description="Lista de títulos de cargo (sin empresa ni fechas exactas)"
    )
    nivel_educacion: Literal["tecnico", "bachiller", "licenciado", "magister", "doctor"]
    carreras: list[str] = Field(
        description="Carreras o especialidades estudiadas"
    )
    certificaciones: list[str] = Field(
        default_factory=list,
        description="Certificaciones profesionales (AWS, PMP, CPA, etc.)"
    )
    idiomas: list[Idioma] = Field(
        description="Lista de idiomas y sus niveles"
    )
    resumen_perfil: str = Field(
        description="Resumen objetivo del perfil profesional en 2-3 oraciones"
    )


class JobDescription(BaseModel):
    """
    Representa la estructura formal de una descripción de puesto de trabajo (Job Description).

    Esta clase se utiliza para estandarizar los requisitos de una oferta laboral, permitiendo
    extraer de forma sistemática los skills técnicos, blandos, años de experiencia y nivel
    educativo requeridos. Facilita la comparación objetiva entre el perfil de un candidato
    y las necesidades reales del puesto.
    """
    jd_id: str = Field(description="UUID interno de la oferta de trabajo")
    titulo_puesto: str = Field(description="Nombre del cargo o posición")
    nivel_requerido: Literal["junior", "semi-senior", "senior", "lead"] = Field(
        description="Nivel de seniority buscado"
    )
    anos_experiencia_min: float = Field(description="Años mínimos de experiencia requerida")
    skills_requeridos: list[str] = Field(description="Habilidades obligatorias (must-have)")
    skills_deseables: list[str] = Field(description="Habilidades valoradas (nice-to-have)")
    industria_preferida: list[str] = Field(description="Sectores de experiencia deseados")
    nivel_educacion_minimo: str = Field(description="Grado académico mínimo requerido")
    idiomas_requeridos: list[Idioma] = Field(description="Lista de idiomas y niveles mínimos")
    descripcion_rol: str = Field(description="Descripción textual de las responsabilidades")

