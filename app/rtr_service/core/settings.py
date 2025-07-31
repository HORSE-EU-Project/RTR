from dotenv import load_dotenv, find_dotenv
import os

# Load environment variables
load_dotenv(find_dotenv())


class Settings:
    """Application settings and configuration"""
    
    # Database settings
    MONGO_USERNAME: str = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
    MONGO_PASSWORD: str = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "qwerty1234")
    MONGO_HOST: str = os.getenv("MONGO_HOST", "mongodb")
    MONGO_PORT: str = os.getenv("MONGO_PORT", "27017")
    MONGO_DATABASE: str = os.getenv("MONGO_DATABASE", "rtr_database")
    
    # Authentication settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = os.getenv("ENCRYPTION_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # EPEM endpoint settings
    EPEM_ENDPOINT: str = os.getenv('EPEM_ENDPOINT', 'http://httpbin.org/post')
    
    # LLM Server settings
    LLM_SERVER_URL: str = os.getenv('LLM_SERVER_URL', 'http://llm-server:8080')
    LLM_SERVER_HOST: str = os.getenv('LLM_SERVER_HOST', 'llm-server')
    LLM_SERVER_PORT: int = int(os.getenv('LLM_SERVER_PORT', '8080'))
    
    # Model settings (legacy - for backward compatibility)
    MODEL_PATH: str = os.getenv('MODEL_PATH', 'llm_server/models/gemma-2b-it.Q4_K_M.gguf')

    @property
    def mongo_url(self) -> str:
        """Construct MongoDB connection URL"""
        return f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/"


# Create global settings instance
settings = Settings()
