from enum import Enum

from pydantic_settings import BaseSettings


class Envs(Enum):
    local_test = "local_test"
    stage = "stage"
    prod = "prod"


class BotSettings(BaseSettings):
    tg_bot_token: str

    postgres_db: str | None = None
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_host: str | None = None

    fsm_redis_host: str | None = None
    fsm_redis_db: int | None = None
    fsm_redis_pass: str | None = None

    register_passphrase: str | None = None
    creator_id: int | None = None

    environment: Envs = Envs.local_test

    inline_kb_button_row_width: int = 2
    schedule_healthcheck: str = "7:00"  # !!!UTC timezone!!!

    class Config:
        env_file = ".env"


settings = BotSettings()
