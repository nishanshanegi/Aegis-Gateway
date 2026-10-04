from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AegisGateway"
    DATABASE_URL: str
    REDIS_URL: str
    UPSTREAM_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()