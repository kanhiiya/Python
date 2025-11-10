from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import get_settings
from app.core.database import Base, engine
from app.api.v1.api import api_router
from starlette.middleware import Middleware as StarletteMiddleware

# custom middleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

settings = get_settings()

# Create tables (keep for simple demos; in production use migrations)
Base.metadata.create_all(bind=engine)

middleware = []

# CORS
if settings.BACKEND_CORS_ORIGINS:
    middleware.append(
        Middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    )

# Force HTTPS if configured (use behind a proxy in production)
if settings.FORCE_HTTPS:
    middleware.append(Middleware(HTTPSRedirectMiddleware))

# Optionally restrict hosts (add your domains to env when deploying)
middleware.append(Middleware(TrustedHostMiddleware, allowed_hosts=["*"]))

# Security headers (always on)
middleware.append(StarletteMiddleware(SecurityHeadersMiddleware))

# Rate limiting (basic in-memory limiter)
middleware.append(StarletteMiddleware(RateLimitMiddleware))

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="A secure FastAPI application with JWT authentication, Redis caching, and comprehensive security middleware.",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",  # Standard FastAPI docs path
    redoc_url="/redoc",  # Standard ReDoc path
    middleware=middleware,
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


def custom_openapi():
    """Custom OpenAPI schema with proper security definitions."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="""
        A secure FastAPI application featuring:
        
        ## Features
        - 🔐 **JWT Authentication**: Secure token-based authentication
        - 🛡️ **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
        - 🚦 **Rate Limiting**: Per-IP request limiting with Redis backend
        - 💾 **Redis Caching**: High-performance data caching
        - 🌐 **CORS Support**: Configurable cross-origin requests
        - 📊 **Comprehensive API**: Full CRUD operations with validation
        
        ## Authentication
        1. **Register**: Create a new user account
        2. **Login**: Get JWT access token
        3. **Authorize**: Use the token for protected endpoints
        
        Click the **Authorize** button below to authenticate with your JWT token.
        """,
        routes=app.routes,
    )
    
    # Add security scheme for JWT Bearer tokens
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token obtained from the login endpoint"
        }
    }
    
    # Apply security to all protected endpoints
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            # Skip login, register, health, and root endpoints
            if path in ["/", "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/health"]:
                continue
                
            openapi_schema["paths"][path][method]["security"] = [
                {"BearerAuth": []}
            ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "api_prefix": "/api/v1",
    }
