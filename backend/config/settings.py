from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ==== CONFIGURACIÓN DEL SERVICIO ====

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # Base de datos
    db_host: str
    db_port: int = Field(default=3306, ge=1, le=65535)
    db_name: str
    db_user: str
    db_password: str
    # Segundos máximos para abrir conexión; evita que una BD caída cuelgue la API.
    db_connect_timeout: int = Field(default=5, ge=1)

    # App
    app_env: str = "development"
    app_port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
