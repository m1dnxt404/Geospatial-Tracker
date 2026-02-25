from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENSKY_USERNAME: str = ""
    OPENSKY_PASSWORD: str = ""
    POLLING_INTERVAL_SECONDS: int = 10
    # NYC bounding box — covers JFK, LGA, EWR airspace
    BBOX_LAMIN: float = 40.5
    BBOX_LOMIN: float = -74.3
    BBOX_LAMAX: float = 41.0
    BBOX_LOMAX: float = -73.7

    class Config:
        env_file = ".env"


settings = Settings()
