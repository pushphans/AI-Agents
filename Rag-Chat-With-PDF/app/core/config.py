from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GROQ_API_KEY: str

    # ========== Vector DB ==========
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # ========== Chunking ==========
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
