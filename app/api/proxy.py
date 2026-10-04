# app/api/proxy.py
import httpx
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.usage_service import log_token_usage
from app.core.config import settings
from app.core.database import get_db
from app.services.cache_service import check_semantic_cache, save_to_semantic_cache
from app.services.circuit_breaker import is_circuit_open, record_failure, record_success
from app.services.pii_shield import redact_pii

router = APIRouter()

# Primary and Fallback Provider URLs
PRIMARY_URL = "https://api.groq.com/openai/v1/chat/completions"
FALLBACK_URL = "https://api.groq.com/openai/v1/chat/completions" 

@router.post("/chat/completions")
async def proxy_chat_completions(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        client_body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    messages = client_body.get("messages", [])
    is_streaming = client_body.get("stream", False)

    # ==========================================
    # 1. PII REDACTION MIDDLEWARE
    # ==========================================
    for message in messages:
        if "content" in message and isinstance(message["content"], str):
            clean_content, found_pii = redact_pii(message["content"])
            if found_pii:
                print(f"🛡️ PII REDACTED! Detected sensitive data types: {found_pii}")
                message["content"] = clean_content

    # Extract the user prompt after redaction
    user_prompt = messages[-1].get("content") if messages else ""

    # ==========================================
    # 2. SEMANTIC CACHE CHECK (Non-streaming only)
    # ==========================================
    if user_prompt and not is_streaming:
        cached_response, hit_type = await check_semantic_cache(db, user_prompt)
        if cached_response:
            print(f"⚡ CACHE HIT ({hit_type}): Returning instantly!")
            return JSONResponse({
                "id": "chatcmpl-cached",
                "object": "chat.completion",
                "choices": [{"message": {"role": "assistant", "content": cached_response}}],
                "x_cache": hit_type 
            })

    # ==========================================
    # 3. CIRCUIT BREAKER & ROUTING
    # ==========================================
    use_fallback = await is_circuit_open()
    target_url = FALLBACK_URL if use_fallback else PRIMARY_URL
    
    if use_fallback:
        print("⚠️ Circuit is OPEN! Routing request to FALLBACK provider.")
    else:
        print("🟢 Routing request to PRIMARY provider.")

    headers = {
        "Authorization": f"Bearer {settings.UPSTREAM_API_KEY}",
        "Content-Type": "application/json"
    }

    client = httpx.AsyncClient(timeout=60.0)

    # Handle Streaming Requests
    if is_streaming:
        async def stream_generator():
            try:
                async with client.stream("POST", target_url, json=client_body, headers=headers) as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk
            finally:
                await client.aclose()
        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    # Handle Non-Streaming Requests
    try:
        response = await client.post(target_url, json=client_body, headers=headers)
        
        # Track failures for Circuit Breaker
        if response.status_code >= 500 or response.status_code == 429:
            if not use_fallback:
                await record_failure()
            raise HTTPException(status_code=response.status_code, detail="Upstream LLM error")

        # Success! Reset circuit breaker
        if not use_fallback:
            await record_success()

# 2. Inside your non-streaming try block, right before returning response_data:
        response_data = response.json()
        answer_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Extract token usage metadata from LLM response
        usage_stats = response_data.get("usage", {})
        model_used = client_body.get("model", "unknown-model")
        
        # Log tokens to PostgreSQL asynchronously (simulating team "Engineering-Alpha")
        if usage_stats:
            await log_token_usage(db, team_id="Engineering-Alpha", model_name=model_used, usage_data=usage_stats)

        # Save new response to Semantic Cache
        if user_prompt and answer_text:
            await save_to_semantic_cache(db, user_prompt, answer_text)
            print("💾 Saved response to Semantic Cache!")

        await client.aclose()
        return JSONResponse(response_data)

    except httpx.RequestError as e:
        if not use_fallback:
            await record_failure()
        await client.aclose()
        raise HTTPException(status_code=502, detail=f"Gateway network error: {str(e)}")