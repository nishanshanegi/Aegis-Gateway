# app/services/cache_service.py
# The Embedding & Search Service
# We need a service that turns text into embeddings and checks Postgres/Redis.
import redis.asyncio as redis
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.cache import SemanticCache

# Load a lightweight, fast local embedding model (runs entirely on your CPU)
embedder = SentenceTransformer("all-MiniLM-L6-v2") # 384 dimensions

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def check_semantic_cache(db: AsyncSession, prompt: str):
    # 1. Redis Exact Match Check
    cached_response = await redis_client.get(f"prompt:{prompt}")
    if cached_response:
        return cached_response, "REDIS_EXACT_HIT"

    # 2. Vector Similarity Search via pgvector
    query_vector = embedder.encode(prompt).tolist()
    
    stmt = (
        select(SemanticCache, SemanticCache.embedding.cosine_distance(query_vector).label("distance"))
        .order_by("distance")
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.first()

    if row:
        cache_obj, distance = row
        # pgvector cosine distance: 0 means identical, 2 means exact opposite.
        # Similarity = 1 - (distance / 2)  OR roughly: distance < 0.2 means high similarity.
        # Let's set a strict distance threshold: distance must be < 0.25 (approx 80%+ similar)
        
        print(f"🔍 Vector Distance Check: {distance}")
        
        if distance < 0.25: 
            return cache_obj.response_text, "VECTOR_SEMANTIC_HIT"
        else:
            print("⚠️ Match found, but similarity is too low. Treating as Cache Miss.")

    return None, "CACHE_MISS"
async def save_to_semantic_cache(db: AsyncSession, prompt: str, response: str):
    """Saves prompt, its vector, and response to Postgres and Redis"""
    vector = embedder.encode(prompt).tolist()
    
    db_cache = SemanticCache(
        prompt_text=prompt,
        embedding=vector,
        response_text=response
    )
    db.add(db_cache)
    await db.commit()

    # Also save exact match to Redis with a 1-hour TTL
    await redis_client.set(f"prompt:{prompt}", response, ex=3600)