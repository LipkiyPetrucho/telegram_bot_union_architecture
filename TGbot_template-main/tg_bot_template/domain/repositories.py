from abc import ABC, abstractmethod

from .models import User


class AbstractUserRepository(ABC):
    @abstractmethod
    async def get_by_social_id(self, social_id: int) -> User | None: ...

    @abstractmethod
    async def add(self, user: User) -> None: ...

    @abstractmethod
    async def update(self, user: User) -> None: ...

    @abstractmethod
    async def list_ordered_by_taps(self) -> list[User]: ...
