# app/services/usage_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.usage import TokenUsageLog

async def log_token_usage(
    db: AsyncSession, 
    team_id: str, 
    model_name: str, 
    usage_data: dict
):
    """
    Persists token consumption metrics to PostgreSQL for cost attribution.
    """
    log_entry = TokenUsageLog(
        team_id=team_id,
        model_name=model_name,
        prompt_tokens=usage_data.get("prompt_tokens", 0),
        completion_tokens=usage_data.get("completion_tokens", 0),
        total_tokens=usage_data.get("total_tokens", 0)
    )
    db.add(log_entry)
    await db.commit()
    print(f"📊 Evaluated & Logged Tokens -> Team: {team_id} | Total: {usage_data.get('total_tokens', 0)}")