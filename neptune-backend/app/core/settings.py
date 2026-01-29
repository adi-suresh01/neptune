import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("NEPTUNE_ENV", "development")
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))

    cors_allow_all: bool = os.getenv("CORS_ALLOW_ALL", "false").lower() == "true"
    cors_origins: List[str] = field(default_factory=lambda: _split_csv(os.getenv("CORS_ORIGINS", "")))

    database_url: str | None = os.getenv("DATABASE_URL")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "5"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    db_pool_pre_ping: bool = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
    db_connect_timeout_seconds: int = int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "5"))

    ollama_url: str = os.getenv("OLLAMA_URL", "http://100.122.73.92:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    ollama_timeout_seconds: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
    ollama_healthcheck: bool = os.getenv("OLLAMA_HEALTHCHECK", "true").lower() == "true"
    ollama_max_retries: int = int(os.getenv("OLLAMA_MAX_RETRIES", "2"))
    ollama_failure_threshold: int = int(os.getenv("OLLAMA_FAILURE_THRESHOLD", "3"))
    ollama_cooldown_seconds: int = int(os.getenv("OLLAMA_COOLDOWN_SECONDS", "30"))

    kg_cache_path: str = os.getenv("KG_CACHE_PATH", "outputs/kg_cache.json")
    kg_cache_ttl_minutes: int = int(os.getenv("KG_CACHE_TTL_MINUTES", "10"))

    s3_endpoint: str | None = os.getenv("S3_ENDPOINT")
    s3_access_key: str | None = os.getenv("S3_ACCESS_KEY")
    s3_secret_key: str | None = os.getenv("S3_SECRET_KEY")
    s3_bucket: str | None = os.getenv("S3_BUCKET")
    s3_region: str | None = os.getenv("S3_REGION")
    s3_secure: bool = os.getenv("S3_SECURE", "true").lower() == "true"
    s3_prefix: str = os.getenv("S3_PREFIX", "neptune/")
    storage_mode: str = os.getenv("STORAGE_MODE", "db").lower()
    s3_connect_timeout_seconds: int = int(os.getenv("S3_CONNECT_TIMEOUT_SECONDS", "3"))
    s3_read_timeout_seconds: int = int(os.getenv("S3_READ_TIMEOUT_SECONDS", "5"))
    s3_max_retries: int = int(os.getenv("S3_MAX_RETRIES", "2"))

    def resolved_cors_origins(self) -> List[str]:
        if self.cors_allow_all:
            return ["*"]
        if self.cors_origins:
            return self.cors_origins
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",
            "tauri://localhost",
            "https://tauri.localhost",
        ]


settings = Settings()
