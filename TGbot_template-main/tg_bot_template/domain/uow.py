from abc import ABC, abstractmethod

from .repositories import AbstractUserRepository


class AbstractUnitOfWork(ABC):
    users: AbstractUserRepository

    async def __aenter__(self):
        return self

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
