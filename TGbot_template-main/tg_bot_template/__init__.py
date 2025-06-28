from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from tg_bot_template.bot_lib.aiogram_overloads import DbDispatcher
from tg_bot_template.config import settings
from tg_bot_template.container import Container
from tg_bot_template.db_infra import setup_db

bot = Bot(token=settings.tg_bot_token)

if settings.environment.local_test:
    storage = MemoryStorage()
else:
    redis = Redis(host=settings.fsm_redis_host, db=settings.fsm_redis_db, password=settings.fsm_redis_pass)
    storage = RedisStorage(redis)

container = Container()
session_factory = setup_db(settings)
container.session_factory.override(session_factory)
container.init_resources()
container.wire(packages=["tg_bot_template"])

dp = DbDispatcher(bot=bot, storage=storage)
dp.set_db_conn(session_factory)
