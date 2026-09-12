import os
from typing import List, Union
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "Flowshield Flash Flood Intelligence"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEMO_MODE: bool = True
    SCENARIO_SEED: int = 26192

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./flowshield.db"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def resolve_sqlite_path(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql://", 1)
            elif v.startswith("sqlite:///./"):
                rel_file = v.replace("sqlite:///./", "")
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                root_db = os.path.join(base_dir, rel_file)
                if os.path.exists(root_db):
                    norm_path = root_db.replace("\\", "/")
                    return f"sqlite:///{norm_path}"
        return v

    # Auth & JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev_jwt_secret_flowshield_sih_2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:80",
        "http://localhost:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Model Artifacts
    MODEL_PATH: str = os.getenv("MODEL_PATH", "ml/models/v2_selected_model.joblib")
    METADATA_PATH: str = os.getenv("METADATA_PATH", "ml/models/v2_decision_pipeline.json")

    # Weather & Meteorological Provider Configuration
    TOMORROW_API_KEY: str = os.getenv("TOMORROW_API_KEY", "")
    TOMORROW_API_BASE_URL: str = os.getenv("TOMORROW_API_BASE_URL", "https://api.tomorrow.io/v4")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", os.getenv("OPENWEATHER_API_KEY", ""))
    WEATHER_API_BASE_URL: str = os.getenv("WEATHER_API_BASE_URL", "https://api.openweathermap.org/data/2.5")
    
    # River Hydrology Provider Configuration
    RIVER_API_KEY: str = os.getenv("RIVER_API_KEY", "")
    
    # AgroMonitoring Configuration
    AGRO_API_KEY: str = os.getenv("AGRO_API_KEY", "")
    AGRO_API_BASE_URL: str = os.getenv("AGRO_API_BASE_URL", "http://api.agromonitoring.com/agro/1.0")

    # Model API Endpoint Configuration
    MODEL_API_URL: str = os.getenv("MODEL_API_URL", "")
    
    # Data Refresh & Polling Interval (in milliseconds, default 5 min = 300,000 ms)
    DATA_REFRESH_INTERVAL_MS: int = int(os.getenv("DATA_REFRESH_INTERVAL_MS", "300000"))

    # AI Providers Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "auto")  # "gemini", "openrouter", "fallback", "auto"
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()
