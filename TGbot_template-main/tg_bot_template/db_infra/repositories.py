from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from tg_bot_template.db_infra.models import users
from tg_bot_template.domain.models import User
from tg_bot_template.domain.repositories import AbstractUserRepository


class SqlAlchemyUserRepository(AbstractUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_social_id(self, social_id: int) -> User | None:
        res = await self._session.execute(select(users).where(users.c.social_id == social_id))
        row = res.mappings().first()
        return User(**row) if row else None

    async def add(self, user: User) -> None:
        await self._session.execute(
            insert(users).values(
                social_id=user.social_id,
                username=user.username,
                registration_date=user.registration_date,
                taps=user.taps,
                name=user.name,
                info=user.info,
                photo=user.photo,
            )
        )

    async def update(self, user: User) -> None:
        await self._session.execute(
            update(users)
            .where(users.c.social_id == user.social_id)
            .values(
                username=user.username,
                taps=user.taps,
                name=user.name,
                info=user.info,
                photo=user.photo,
            )
        )

    async def list_ordered_by_taps(self) -> list[User]:
        res = await self._session.execute(select(users).order_by(users.c.taps.desc()))
        return [User(**row) for row in res.mappings().all()]
