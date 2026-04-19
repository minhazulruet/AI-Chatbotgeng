"""
Configuration Management
"""
import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "AI Chatbot"
    debug: bool = True
    environment: str = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", 10000))  # Read from env or default to 10000
    
    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS - Read from environment variable or use defaults
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*"  # Allow all in development/production - frontend served from same origin
    ]
    
    # RAG Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    faiss_index_path: str = "./data/processed/index.faiss"
    chunks_pkl_path: str = "./data/processed/chunks.pkl"
    
    # Database
    database_url: str = "sqlite:///./test.db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
