"""Configuration centralisée — jamais de secret codé en dur.
EN: Centralized settings; secrets come from env vars only.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://riverside:changeme@localhost:5432/riverside"
    stac_api_url: str = "https://earth-search.aws.element84.com/v1"
    default_collection: str = "sentinel-2-l2a"
    max_cloud_cover: float = 20.0
    ndvi_alert_threshold: float = 0.30
    allowed_origins: str = "http://localhost:3000"
    # Webhook n8n pour alertes critiques — None = désactivé / disabled when unset
    n8n_webhook_url: str | None = None


settings = Settings()
