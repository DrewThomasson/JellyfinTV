import os
from pydantic import BaseModel

class Settings(BaseModel):
    JELLYFIN_URL: str = ""
    JELLYFIN_USERNAME: str = ""
    JELLYFIN_PASSWORD: str = ""
    JELLYFIN_TOKEN: str = ""
    JELLYFIN_USER_ID: str = ""
    
    # Database
    DATABASE_URL: str = "sqlite:///./jellyfintv.db"

settings = Settings()
