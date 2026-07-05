from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEEPSEEK_API_KEY: str
    LANGSMITH_TRACING: bool = True
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str 

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
