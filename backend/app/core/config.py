from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str = "dev-secret-change-in-production"
    FRONTEND_URL: str = "http://localhost:5173"
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

