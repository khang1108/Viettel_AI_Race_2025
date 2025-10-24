from pydantic import BaseModel
import os

class Settings(BaseModel):
    pg_dsn: str = (
        f"postgresql+psycopg2://{os.getenv('PGUSER')}:{os.getenv('PGPASSWORD')}"
        f"@{os.getenv('PGHOST')}:{os.getenv('PGPORT')}/{os.getenv('PGDATABASE')}"
    )
    celery_broker: str = os.getenv("CELERY_BROKER_URL")
    celery_backend: str = os.getenv("CELERY_RESULT_BACKEND")
    upload_dir: str = os.getenv("UPLOAD_DIR", "/app/data/uploads")
    embed_model_name: str = os.getenv("EMBEDDING_MODEL")
    embed_dim: int = int(os.getenv("EMBED_DIM", "384"))
    top_k: int = int(os.getenv("TOP_K", "6"))

settings = Settings()
