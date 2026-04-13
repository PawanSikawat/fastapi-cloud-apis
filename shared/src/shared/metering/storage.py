import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.models import UsageRecord


async def flush_usage_to_db(
    db_session: AsyncSession,
    api_key_id: str,
    api_name: str,
    month: str,
    count: int,
) -> None:
    """Persist Redis usage counter to PostgreSQL."""
    result = await db_session.execute(
        select(UsageRecord).where(
            UsageRecord.api_key_id == uuid.UUID(api_key_id),
            UsageRecord.api_name == api_name,
            UsageRecord.month == month,
        )
    )
    record = result.scalar_one_or_none()

    if record:
        record.request_count = count
    else:
        record = UsageRecord(
            api_key_id=uuid.UUID(api_key_id),
            api_name=api_name,
            month=month,
            request_count=count,
        )
        db_session.add(record)

    await db_session.commit()
