from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.config import get_settings


# echo=False means don't print every SQL query (set True for debugging)
settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False)

# Session factory -- each request gets its own session
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """
    Dependency for FastAPI routes.
    
    HOW IT'S USED:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    
    The 'yield' makes it a context manager:
    - Creates a session before the route runs
    - Closes the session after the route finishes
    - Even if an error occurs, the session is closed
    """
    async with async_session() as session:
        yield session
