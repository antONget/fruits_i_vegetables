from sqlalchemy import BigInteger, ForeignKey, String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

from typing import List

engine = create_async_engine(url="sqlite+aiosqlite:///database/db.sqlite3", echo=False)
# engine = create_async_engine(url="sqlite+aiosqlite:///db.sqlite3", echo=False)


async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(200))
    referral_link: Mapped[str] = mapped_column(String(200), default="None")
    referral_users: Mapped[str] = mapped_column(String, default="")
    referer_id: Mapped[int] = mapped_column(Integer, default=0)
    balance: Mapped[int] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(200), default="None")


class Price(Base):
    __tablename__ = 'prices'

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(200))
    product: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200))
    price: Mapped[str] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String)


class Order(Base):
    __tablename__ = 'order'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_order: Mapped[int] = mapped_column(String(200))
    telegram_id: Mapped[int] = mapped_column(Integer)
    address_order: Mapped[int] = mapped_column(String(200), default="none")
    comment: Mapped[int] = mapped_column(String(200), default="none")
    status: Mapped[int] = mapped_column(String(50), default='create')


class Item(Base):
    __tablename__ = 'item'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_order: Mapped[int] = mapped_column(String(200))
    telegram_id: Mapped[int] = mapped_column(Integer)
    item: Mapped[str] = mapped_column(String(200))
    count: Mapped[int] = mapped_column(Integer)
    price: Mapped[int] = mapped_column(Integer)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

# import asyncio
# #
# asyncio.run(async_main())
