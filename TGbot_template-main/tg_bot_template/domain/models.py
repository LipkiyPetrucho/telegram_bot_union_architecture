from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int | None
    social_id: int
    username: str | None
    registration_date: datetime | None
    taps: int = 0
    name: str | None = None
    info: str | None = None
    photo: str | None = None
