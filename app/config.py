"""Configuration management using Pydantic Settings"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # MongoDB Configuration
    MONGODB_URI: str
    
    # Security Keys
    AES_ENCRYPTION_KEY: str  # 64 hex characters (32 bytes)
    API_SECRET_KEY: str = "default-secret-key-change-in-production"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # CORS Configuration
    CORS_ORIGINS: str = "*"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_aes_key_bytes(self) -> bytes:
        """Convert hex encryption key to bytes"""
        try:
            return bytes.fromhex(self.AES_ENCRYPTION_KEY)
        except ValueError:
            raise ValueError(
                "AES_ENCRYPTION_KEY must be a 64-character hexadecimal string (32 bytes)"
            )
    
    def get_cors_origins_list(self) -> list:
        """Parse CORS origins from comma-separated string"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
