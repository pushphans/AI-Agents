from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DEEPSEEK_API_KEY: str
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str = "A2.3-Ecommerce Shopping Assistant"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()