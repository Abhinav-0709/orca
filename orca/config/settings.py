"""Configuration settings for ORCA."""

from typing import Any, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ORCA runtime settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General Environment
    orca_env: Literal["development", "testing", "production"] = Field(
        default="development",
        description="Operating environment stage",
    )
    orca_log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Operational Data Sources
    incois_base_url: str = Field(
        default="https://www.incois.gov.in",
        description="INCOIS portal / API base URL",
    )
    open_meteo_base_url: str = Field(
        default="https://marine-api.open-meteo.com/v1/marine",
        description="Open-Meteo Marine API base URL (no API key required)",
    )
    imd_api_base_url: str = Field(
        default="https://api.imd.gov.in",
        description="IMD API base URL (optional bulletin source)",
    )
    imd_api_key: str | None = Field(
        default=None,
        description="IMD API access key",
    )

    # Reliability and local evidence persistence
    data_source_max_attempts: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum attempts for transient live data-source failures",
    )
    data_source_retry_base_delay_seconds: float = Field(
        default=0.25,
        ge=0.0,
        le=5.0,
        description="Initial retry delay before exponential backoff",
    )
    data_source_retry_max_delay_seconds: float = Field(
        default=2.0,
        ge=0.0,
        le=30.0,
        description="Maximum delay between live data-source attempts",
    )
    evidence_store_path: str | None = Field(
        default=None,
        description="Optional SQLite path for durable evidence and assessments",
    )

    @field_validator(
        "evidence_store_path",
        "imd_api_key",
        "agentverse_api_key",
        "agentverse_mailbox_key",
        "acp_endpoint",
        "llm_api_key",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            return None
        return v

    # Fetch Ecosystem / Agentverse
    agentverse_api_key: str | None = Field(
        default=None,
        description="Agentverse API key for registration & discovery",
    )
    agentverse_mailbox_key: str | None = Field(
        default=None,
        description="Agentverse Mailbox key for remote communication",
    )
    acp_endpoint: str | None = Field(
        default=None,
        description="Agent Chat Protocol endpoint",
    )

    # LLM / Reasoning Layer
    llm_provider: str = Field(
        default="asi1",
        description="LLM provider (asi1, gemini, openai, etc.)",
    )
    llm_api_key: str | None = Field(
        default=None,
        description="API key for LLM provider",
    )
    llm_model: str = Field(
        default="asi1-mini",
        description="Default model name for intent and reasoning",
    )

    # Geospatial Settings
    default_search_radius_km: float = Field(
        default=30.0,
        ge=1.0,
        le=200.0,
        description="Default candidate search radius in km",
    )
    max_search_radius_km: float = Field(
        default=100.0,
        ge=5.0,
        le=300.0,
        description="Maximum allowed search radius in km",
    )
    restricted_zone_buffer_km: float = Field(
        default=5.0,
        ge=0.0,
        description="Safety buffer margin around restricted boundaries in km",
    )


# Global singleton instance
settings = Settings()
