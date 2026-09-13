from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Central application configuration.

    All values can be overridden through environment variables
    or the .env file.
    """

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    app_name: str = "Kernel Sovereign Agentic AI Workbench"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False

    api_prefix: str = "/api/v1"

    # ------------------------------------------------------------------
    # Server
    # ------------------------------------------------------------------

    host: str = "0.0.0.0"
    port: int = 8000

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    database_url: str = Field(
        default="postgresql+asyncpg://kernel:kernel@localhost:5432/kernel",
        description="PostgreSQL async connection URL",
    )

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------

    redis_url: str = "redis://localhost:6379/0"

    # ------------------------------------------------------------------
    # Local LLM
    # ------------------------------------------------------------------

    llm_provider: str = "local"

    local_llm_base_url: str = "http://localhost:8001"

    local_llm_model: str = "local-model"

    llm_timeout_seconds: int = 120

    # ------------------------------------------------------------------
    # Embeddings / RAG
    # ------------------------------------------------------------------

    embedding_model: str = "BAAI/bge-small-en-v1.5"

    qdrant_url: str = "http://localhost:6333"

    qdrant_collection: str = "kernel_knowledge"

    rag_top_k: int = 5

    # ------------------------------------------------------------------
    # OCR / Vision
    # ------------------------------------------------------------------

    ocr_enabled: bool = True

    ocr_language: str = "en"

    # ------------------------------------------------------------------
    # Agent configuration
    # ------------------------------------------------------------------

    default_confidence_threshold: float = 0.90

    max_agent_iterations: int = 10

    agent_timeout_seconds: int = 180

    # ------------------------------------------------------------------
    # Capability Marketplace
    # ------------------------------------------------------------------

    capability_registry_url: str = (
        "http://localhost:9000"
    )

    capability_request_timeout_seconds: int = 60

    # ------------------------------------------------------------------
    # Privacy / Security
    # ------------------------------------------------------------------

    privacy_enabled: bool = True

    anonymization_enabled: bool = True

    allow_external_capabilities: bool = True

    # Maximum amount an agent can autonomously spend
    # on external capabilities.
    max_autonomous_spend: float = 1.00

    # ------------------------------------------------------------------
    # x402 / GoPlausible
    # ------------------------------------------------------------------

    x402_enabled: bool = True

    x402_network: str = "algorand-testnet"

    x402_facilitator_url: str = "https://facilitator.goplausible.com"

    x402_timeout_seconds: int = 30

    # ------------------------------------------------------------------
    # Algorand
    # ------------------------------------------------------------------

    algorand_network: str = "testnet"

    algorand_node_url: str = (
        "https://testnet-api.algonode.cloud"
    )

    algorand_indexer_url: str = (
        "https://testnet-idx.algonode.cloud"
    )

    # NEVER put the real private key directly in source code.
    algorand_private_key: str | None = None

    algorand_wallet_address: str | None = None

    # ------------------------------------------------------------------
    # File handling
    # ------------------------------------------------------------------

    upload_directory: str = str(BASE_DIR / "data" / "documents")

    knowledge_base_directory: str = str(
        BASE_DIR / "data" / "knowledge_base"
    )

    max_upload_size_mb: int = 50

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------

    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    log_level: str = "INFO"

    # ------------------------------------------------------------------
    # JWT / Authentication
    # ------------------------------------------------------------------

    jwt_secret_key: str = "CHANGE_THIS_IN_PRODUCTION"

    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 60

    # ------------------------------------------------------------------
    # Pydantic Settings configuration
    # ------------------------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Helper properties
    # ------------------------------------------------------------------

    @property
    def cors_origin_list(self) -> list[str]:
        """Convert comma-separated CORS origins into a list."""
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Using a cached instance prevents repeatedly parsing the
    environment configuration throughout the application.
    """
    return Settings()


settings = get_settings()