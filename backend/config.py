import os
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    
    # TURN Server Configuration
    TURN_SERVER_URL: str = os.getenv("TURN_SERVER_URL", "turn:global.turn.twilio.com:3478")
    TURN_USERNAME: str = os.getenv("TURN_USERNAME", "")
    TURN_CREDENTIAL: str = os.getenv("TURN_CREDENTIAL", "")
    
    # External API
    PERSONA_FETCHER_API_URL: str = os.getenv("PERSONA_FETCHER_API_URL", "https://persona-fetcher-api.up.railway.app/personas")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    
    # Session Configuration
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "your-secret-key-change-in-production")
    SESSION_EXPIRE_MINUTES: int = int(os.getenv("SESSION_EXPIRE_MINUTES", "60"))

settings = Settings()
