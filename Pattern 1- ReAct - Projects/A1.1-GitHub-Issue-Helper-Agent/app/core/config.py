from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    GITHUB_TOKEN: str

    LANGSMITH_TRACING = True
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT = "A1.1-GitHub-Issue-Helper-Agent"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
