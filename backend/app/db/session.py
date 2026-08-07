from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Defaults (pool_size=5, max_overflow=10) cap the app at 15 concurrent DB
# connections even though Postgres itself allows up to 100 -- raised to give
# real headroom under concurrent load. pool_pre_ping avoids "stale
# connection" errors after Railway recycles idle connections.
engine = create_engine(settings.database_url, pool_size=20, max_overflow=20, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
