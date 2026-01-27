from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import select
from typing import AsyncGenerator
from app.config import settings

Base = declarative_base()
engine = None
async_session_maker = None


async def init_db():
    global engine, async_session_maker
    
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        future=True
    )
    
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Import models to create tables
    from app.models.heat_exchanger import HeatExchanger
    from app.models.monitoring_data import MonitoringData
    from app.models.settings import SystemSettings
    from app.models.user import User
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create default admin user if no users exist
    async with async_session_maker() as session:
        result = await session.execute(select(User).limit(1))
        if not result.scalar_one_or_none():
            default_admin = User(
                username="admin",
                hashed_password=User.hash_password("admin"),
                is_admin=True
            )
            session.add(default_admin)
            await session.commit()
            print("[OK] Default admin user created (username: admin, password: admin)")
    
    print("[OK] Database initialized")


async def close_db():
    global engine
    if engine:
        await engine.dispose()
        print("Database connection closed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
