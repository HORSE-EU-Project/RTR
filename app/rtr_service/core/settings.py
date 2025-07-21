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
    
    # Model settings
    MODEL_PATH: str = os.getenv('MODEL_PATH', 'models/gemma-2b-it.Q4_K_M.gguf')
    
    @property
    def mongo_url(self) -> str:
        """Construct MongoDB connection URL"""
        return f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/"


# Create global settings instance
settings = Settings()
