from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./cooling_monitor.db"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Redfish
    redfish_username: str = "admin"
    redfish_password: str = "password"
    redfish_verify_ssl: bool = False
    
    # Monitoring
    polling_interval_seconds: int = 30
    
    # Email settings - now managed in database, these are fallbacks only
    smtp_enabled: bool = False
    smtp_server: str = "smtp.office365.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_to_emails: List[str] = []
    smtp_use_tls: bool = True
    pump_flow_critical_threshold: float = 10.0
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production-min-32-chars"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
