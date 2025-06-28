from dataclasses import dataclass

from aiogram.fsm.state import State, StatesGroup


@dataclass
class UserFormData:
    name: str
    info: str
    photo: str


class UserForm(StatesGroup):  # type: ignore[misc]
    name = State()
    info = State()
    photo = State()
