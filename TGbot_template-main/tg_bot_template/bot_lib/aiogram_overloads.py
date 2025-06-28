from aiogram import Dispatcher, types
from aiogram.fsm.storage.base import BaseStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class DbDispatcher(Dispatcher):  # type: ignore[misc]
    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self._db_conn: async_sessionmaker[AsyncSession] | None = None

    def set_db_conn(self, conn: async_sessionmaker[AsyncSession]) -> None:
        self._db_conn = conn

    def get_db_conn(self) -> async_sessionmaker[AsyncSession]:
        return self._db_conn


class AbsFilter:  # type: ignore[misc]
    key = "key"

    def __init__(self, **kwargs):  # type: ignore[no-untyped-def]
        setattr(self, self.key, kwargs[self.key])

    async def check(self, msg: types.Message) -> bool:
        return True
