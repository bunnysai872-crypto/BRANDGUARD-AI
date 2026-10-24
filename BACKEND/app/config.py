import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "brandguard-default-secret-key-change-in-prod")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "brandguard-default-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    
    # Handle Render / Supabase / Neon PostgreSQL URL standard fix (postgres:// -> postgresql://)
    db_url = os.getenv("DATABASE_URL", "sqlite:///brandguard.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Production-ready connection pooling for PostgreSQL
    if not db_url.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": int(os.getenv("DB_POOL_SIZE", 5)),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", 10)),
            "pool_pre_ping": True,
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", 300)),
        }
    
    # CORS Origins configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    
    # Gemini AI configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # Validate secret key safety in production
    if Config.SECRET_KEY == "brandguard-default-secret-key-change-in-prod":
        import warnings
        warnings.warn(
            "CRITICAL SECURITY: Running in production with default SECRET_KEY! "
            "Set a secure SECRET_KEY in your environment variables.",
            stacklevel=2
        )

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-jwt-secret-key-32-characters-minimum-secure"
    SECRET_KEY = "test-secret-key-32-characters-minimum-secure"

config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}
