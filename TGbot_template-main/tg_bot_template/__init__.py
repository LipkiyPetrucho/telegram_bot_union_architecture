from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from tg_bot_template.bot_lib.aiogram_overloads import DbDispatcher
from tg_bot_template.config import settings
from tg_bot_template.container import Container
from tg_bot_template.db_infra import setup_db

if settings.environment.local_test:
    storage = MemoryStorage()
else:
    storage = RedisStorage2(settings.fsm_redis_host, db=settings.fsm_redis_db, password=settings.fsm_redis_pass)

container = Container()
session_factory = setup_db(settings)
container.session_factory.override(session_factory)
container.init_resources()
container.wire(packages=["tg_bot_template"])

dp = DbDispatcher(Bot(token=settings.tg_bot_token), storage=storage)  # type: ignore[no-untyped-call]
dp.set_db_conn(session_factory)
