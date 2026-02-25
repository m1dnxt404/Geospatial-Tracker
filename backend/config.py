from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENSKY_USERNAME: str = ""
    OPENSKY_PASSWORD: str = ""
    POLLING_INTERVAL_SECONDS: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
