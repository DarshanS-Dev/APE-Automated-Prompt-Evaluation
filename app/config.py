from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    groq_api_key: str
    groq_base_url: str

    class Config:
        env_file= ".env"

settings = Settings()