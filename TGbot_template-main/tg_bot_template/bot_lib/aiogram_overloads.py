from aiogram import Bot, Dispatcher, types
from aiogram.filters import BaseFilter
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class DbDispatcher(Dispatcher):  # type: ignore[misc]
    def __init__(self, *, bot: Bot, storage=None, **kwargs) -> None:
        super().__init__(storage=storage, **kwargs)
        self.bot = bot
        self._db_conn: async_sessionmaker[AsyncSession] | None = None

    def set_db_conn(self, conn: async_sessionmaker[AsyncSession]) -> None:
        self._db_conn = conn

    def get_db_conn(self) -> async_sessionmaker[AsyncSession]:
        return self._db_conn


class AbsFilter(BaseFilter):  # type: ignore[misc]
    key = "key"

    def __init__(self, **kwargs):  # type: ignore[no-untyped-def]
        setattr(self, self.key, kwargs[self.key])

    async def __call__(self, msg: types.Message) -> bool:
        return True
