from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./trustmatch.db"
    SECRET_KEY: str = "dev-secret-change-in-production"
    FRONTEND_URL: str = "http://localhost:5173"
    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

