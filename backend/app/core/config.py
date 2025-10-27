from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Paths 
    UPLOAD_DIR: str = "/data/uploads"
    DATA_DIR: str = "/data"  # Base data directory
    
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "rag"
    
    # LLM Settings
    LLM_MODEL_PATH: str = "deepseek-ai/deepseek-ocr"
    LLM_MAX_LENGTH: int = 512
    LLM_TEMPERATURE: float = 0.7
    
    # DB Pool Settings
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # RabbitMQ
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASS: str = "guest"
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_VHOST: str = "/"
    
    # Embedding 
    EMBED_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBED_DIM: int = 384
    SENTENCE_TRANSFORMERS_HOME: str = "/models"  # Model cache location

    @property
    def DATABASE_URL(self) -> str:
        """Async database URL for SQLAlchemy"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Sync database URL for Celery tasks"""
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"
    
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return "rpc://"

    class Config:
        env_file = ".env"

settings = Settings()