from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Smart LandGuard BD"
    demo_mode: bool = True
    api_prefix: str = "/api"


settings = Settings()
