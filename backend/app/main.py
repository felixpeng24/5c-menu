from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db
from app.redis import create_redis
from app.routers import admin, halls, menus, open_now

# Ensure all models are imported so create_all sees them
import app.models.parser_run  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: DB tables, Redis connection."""
    await init_db()
    settings = get_settings()
    app.state.redis = create_redis(settings.redis_url)
    yield
    await app.state.redis.aclose()


app = FastAPI(title="5C Menu API", version="2.0.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(halls.router, prefix="/api/v2/halls")
app.include_router(menus.router, prefix="/api/v2/menus")
app.include_router(open_now.router, prefix="/api/v2/open-now")
app.include_router(admin.router, prefix="/api/v2/admin")
