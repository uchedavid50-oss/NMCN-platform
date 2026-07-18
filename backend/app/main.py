from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

from app.api.auth import router as auth_router
from app.api.subjects import router as subjects_router
from app.api.topics import router as topics_router
from app.api.questions import router as questions_router
from app.api.practice import router as practice_router
from app.api.mock import router as mock_router
from app.api.payments import router as payments_router
from app.api.analytics import router as analytics_router
from app.api.tutor import router as tutor_router
from app.api.flashcards import router as flashcards_router
from app.api.notes import router as notes_router
from app.api.games import router as games_router
from app.core.config import settings

DEV_DEFAULT_JWT_SECRET = "dev-only-change-this-before-any-real-deployment"

if settings.environment == "production" and settings.jwt_secret_key == DEV_DEFAULT_JWT_SECRET:
    # Fail fast and loud rather than silently running a production deployment
    # with a publicly-known JWT signing key — that would let anyone forge
    # valid login tokens for any user, including admins.
    raise RuntimeError(
        "Refusing to start: ENVIRONMENT=production but JWT_SECRET_KEY is still the "
        "development default. Set a real, random JWT_SECRET_KEY before deploying."
    )

app = FastAPI(title="NMCN Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine(settings.database_url)

# Schema is now managed by Alembic migrations (see migrations/), not by SQLAlchemy's
# create_all. Run `docker compose exec backend alembic upgrade head` after starting
# the containers, before hitting any endpoint below.

app.include_router(auth_router)
app.include_router(subjects_router)
app.include_router(topics_router)
app.include_router(questions_router)
app.include_router(practice_router)
app.include_router(mock_router)
app.include_router(payments_router)
app.include_router(analytics_router)
app.include_router(tutor_router)
app.include_router(flashcards_router)
app.include_router(notes_router)
app.include_router(games_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        value = result.scalar()
    return {"status": "ok", "db_result": value}
