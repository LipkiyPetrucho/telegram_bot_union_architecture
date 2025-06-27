from dependency_injector import containers, providers

from tg_bot_template.config import settings
from tg_bot_template.db_infra import setup_db
from tg_bot_template.db_infra.unit_of_work import SqlAlchemyUnitOfWork


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["tg_bot_template"])

    session_factory = providers.Singleton(setup_db, settings)
    unit_of_work = providers.Factory(SqlAlchemyUnitOfWork, session_factory=session_factory)
