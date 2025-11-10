from fastapi import FastAPI
from app.core.config import get_settings
from app.core.database import Base, engine
from app.api.v1.api import api_router

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/docs"
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/api/docs"
    }
