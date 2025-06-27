from datetime import datetime, timezone

from aiocache import cached
from aiocache.serializers import PickleSerializer
from dependency_injector.wiring import Provide, inject
from loguru import logger

from tg_bot_template.bot_infra.states import UserFormData
from tg_bot_template.bot_lib.bot_feature import TgUser
from tg_bot_template.container import Container
from tg_bot_template.domain.models import User
from tg_bot_template.domain.uow import AbstractUnitOfWork


@inject
async def check_user_registered(*, tg_user: TgUser, uow: AbstractUnitOfWork = Provide[Container.unit_of_work]) -> bool:
    async with uow:
        return await uow.users.get_by_social_id(tg_user.tg_id) is not None


@cached(ttl=0.2, serializer=PickleSerializer())
@inject
async def get_user_for_filters(
    *, tg_user: TgUser, uow: AbstractUnitOfWork = Provide[Container.unit_of_work]
) -> User | None:
    return await get_user(tg_user=tg_user, uow=uow)


@inject
async def get_user(*, tg_user: TgUser, uow: AbstractUnitOfWork = Provide[Container.unit_of_work]) -> User | None:
    async with uow:
        user = await uow.users.get_by_social_id(tg_user.tg_id)
        if user is not None:
            user.username = tg_user.username
            await uow.users.update(user)
        return user


@inject
async def create_user(*, tg_user: TgUser, uow: AbstractUnitOfWork = Provide[Container.unit_of_work]) -> None:
    user = User(
        id=None,
        social_id=tg_user.tg_id,
        username=tg_user.username,
        registration_date=datetime.now(timezone.utc),
    )
    async with uow:
        await uow.users.add(user)
    logger.info(f"New user[{tg_user.username}] registered")


@inject
async def update_user_info(
    *,
    tg_user: TgUser,
    user_form_data: UserFormData,
    uow: AbstractUnitOfWork = Provide[Container.unit_of_work],
) -> None:
    async with uow:
        user = await uow.users.get_by_social_id(tg_user.tg_id)
        if user is not None:
            user.name = user_form_data.name
            user.info = user_form_data.info
            user.photo = user_form_data.photo
            await uow.users.update(user)


@inject
async def incr_user_taps(*, tg_user: TgUser, uow: AbstractUnitOfWork = Provide[Container.unit_of_work]) -> None:
    async with uow:
        user = await uow.users.get_by_social_id(tg_user.tg_id)
        if user is not None:
            user.taps += 1
            await uow.users.update(user)


@inject
async def get_all_users(
    uow: AbstractUnitOfWork = Provide[Container.unit_of_work],
) -> list[User]:
    async with uow:
        return await uow.users.list_ordered_by_taps()
