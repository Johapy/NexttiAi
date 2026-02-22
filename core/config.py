# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    odoo_url: str
    odoo_db: str
    odoo_username: str
    odoo_password: str
    gemini_api_key: str

    class Config:
        env_file = ".env"

# Creamos una instancia global para usarla en todo el proyecto
settings = Settings()