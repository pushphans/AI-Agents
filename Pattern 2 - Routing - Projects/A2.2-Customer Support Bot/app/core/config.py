from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    chroma_persist_dir: str = "./data/chroma_db"
    chroma_collection_name: str = "company_faq"
    deepseek_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
