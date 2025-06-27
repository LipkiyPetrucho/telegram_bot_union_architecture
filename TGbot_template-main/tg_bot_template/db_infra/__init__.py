from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tg_bot_template.config import BotSettings
from tg_bot_template.db_infra.models import metadata


def setup_db(settings: BotSettings) -> async_sessionmaker[AsyncSession]:
    url = (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}/{settings.postgres_db}"
    )
    engine = create_async_engine(url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async def init_models() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    asyncio.run(init_models())
    return async_session
