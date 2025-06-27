from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tg_bot_template.db_infra.repositories import SqlAlchemyUserRepository
from tg_bot_template.domain.repositories import AbstractUserRepository
from tg_bot_template.domain.uow import AbstractUnitOfWork


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        self.users: AbstractUserRepository = SqlAlchemyUserRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc is None:
            await self.commit()
        else:
            await self.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
