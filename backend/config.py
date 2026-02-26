from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENSKY_CLIENT_ID: str = ""
    OPENSKY_CLIENT_SECRET: str = ""
    OPENSKY_USERNAME: str = ""
    OPENSKY_PASSWORD: str = ""
    ADSB_API_KEY: str = ""
    POLLING_INTERVAL_SECONDS: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
