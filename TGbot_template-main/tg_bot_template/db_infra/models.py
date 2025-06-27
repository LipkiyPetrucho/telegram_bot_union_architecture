from sqlalchemy import BigInteger, Column, DateTime, Integer, MetaData, String, Table, Text

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("social_id", BigInteger, nullable=False, unique=True),
    Column("username", String(50)),
    Column("registration_date", DateTime),
    Column("taps", BigInteger, default=0),
    Column("name", Text),
    Column("info", Text),
    Column("photo", Text),
)
