from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.redis import create_redis
from app.routers import halls


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: Redis connection."""
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
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(halls.router, prefix="/api/v2/halls")
# TODO: app.include_router(menus.router, prefix="/api/v2/menus")  -- plan 02-02
# TODO: app.include_router(open_now.router, prefix="/api/v2/open-now")  -- plan 02-03
