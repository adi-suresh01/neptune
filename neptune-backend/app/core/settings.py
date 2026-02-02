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
    app_mode: str = os.getenv("NEPTUNE_MODE", "server").lower()
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    db_backend: str = os.getenv("DB_BACKEND", "auto").lower()
    desktop_data_dir: str = os.getenv(
        "NEPTUNE_DESKTOP_DIR",
        os.path.join(os.path.expanduser("~"), ".neptune"),
    )

    cors_allow_all: bool = os.getenv("CORS_ALLOW_ALL", "false").lower() == "true"
    cors_origins: List[str] = field(default_factory=lambda: _split_csv(os.getenv("CORS_ORIGINS", "")))

    database_url: str | None = os.getenv("DATABASE_URL")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "5"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    db_pool_pre_ping: bool = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
    db_connect_timeout_seconds: int = int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "5"))

    ollama_url: str = os.getenv("OLLAMA_URL", "http://100.122.73.92:11434")
    ollama_shared: bool = os.getenv("OLLAMA_SHARED", "true").lower() == "true"
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    ollama_timeout_seconds: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
    ollama_connect_timeout_seconds: float = float(os.getenv("OLLAMA_CONNECT_TIMEOUT_SECONDS", "5"))
    ollama_healthcheck: bool = os.getenv("OLLAMA_HEALTHCHECK", "true").lower() == "true"
    ollama_max_retries: int = int(os.getenv("OLLAMA_MAX_RETRIES", "2"))
    ollama_failure_threshold: int = int(os.getenv("OLLAMA_FAILURE_THRESHOLD", "3"))
    ollama_cooldown_seconds: int = int(os.getenv("OLLAMA_COOLDOWN_SECONDS", "30"))
    ollama_temperature: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
    ollama_top_p: float = float(os.getenv("OLLAMA_TOP_P", "0.9"))
    ollama_max_tokens: int = int(os.getenv("OLLAMA_MAX_TOKENS", "128"))
    llm_prompt_version: str = os.getenv("LLM_PROMPT_VERSION", "v1")
    llm_topic_batch_size: int = int(os.getenv("LLM_TOPIC_BATCH_SIZE", "8"))
    llm_relationship_batch_size: int = int(os.getenv("LLM_REL_BATCH_SIZE", "20"))
    llm_max_concurrency: int = int(os.getenv("LLM_MAX_CONCURRENCY", "4"))
    llm_max_queue: int = int(os.getenv("LLM_MAX_QUEUE", "16"))

    kg_cache_path: str = os.getenv("KG_CACHE_PATH", "outputs/kg_cache.json")
    kg_cache_ttl_minutes: int = int(os.getenv("KG_CACHE_TTL_MINUTES", "10"))
    kg_cache_version: str = os.getenv("KG_CACHE_VERSION", "v1")
    max_note_bytes: int = int(os.getenv("MAX_NOTE_BYTES", "1048576"))
    min_note_chars: int = int(os.getenv("MIN_NOTE_CHARS", "1"))
    kg_min_strength: float = float(os.getenv("KG_MIN_STRENGTH", "0.2"))
    kg_max_edges: int = int(os.getenv("KG_MAX_EDGES", "500"))
    max_note_revisions: int = int(os.getenv("MAX_NOTE_REVISIONS", "20"))

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

    vector_backend: str = os.getenv("VECTOR_BACKEND", "none").lower()
    search_mode: str = os.getenv("SEARCH_MODE", "auto").lower()
    search_min_query_len: int = int(os.getenv("SEARCH_MIN_QUERY_LEN", "2"))
    search_max_results: int = int(os.getenv("SEARCH_MAX_RESULTS", "50"))

    def resolved_cors_origins(self) -> List[str]:
        if self.environment == "production" and self.cors_allow_all:
            if self.cors_origins:
                return self.cors_origins
            return []
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
