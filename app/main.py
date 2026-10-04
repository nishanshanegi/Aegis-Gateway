# app/main.py
from fastapi import FastAPI
from sqlalchemy import text # <-- 1. Import text
from app.api.proxy import router as proxy_router
from app.core.config import settings
from app.core.database import engine, Base
from app.models.cache import SemanticCache 
from app.models.usage import TokenUsageLog

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        # 2. Wrap the raw string in text()
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(Base.metadata.create_all)

app.include_router(proxy_router, prefix="/v1", tags=["Gateway Proxy"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AegisGateway"}