from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.core.config import get_settings
from app.db import Base, SessionLocal, engine
from app.services.seed import seed_database

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session)


@app.get("/health")
def health():
    return {"status": "ok", "product": settings.app_name}


@app.get("/")
def root():
    return {
        "product": settings.app_name,
        "status": "live",
        "docs": "/docs",
        "api": "/api",
        "health": "/health",
    }


app.include_router(router)
