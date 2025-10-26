from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text 
from app.db.session import engine
from app.models import Base
import logging

logger = logging.getLogger(__name__)

async def init_db(drop_all: bool = False):
    """
    Initialize database tables
    
    Args:
        drop_all: If True, drop all tables before creating (use with caution!)
    """
    async with engine.begin() as conn:
        if drop_all:
            logger.warning("Dropping all tables...")
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        
        # Enable pgvector extension (safe if already exists)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
    logger.info("Database initialization complete")

if __name__ == "__main__":
    import asyncio
    from sqlalchemy import text
    
    # Run with drop_all=False by default for safety
    asyncio.run(init_db(drop_all=False))