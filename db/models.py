from sqlalchemy import *
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine
import os

# Определение относительного пути к файлу базы данных
database_name = 'blacklist.db'
relative_path = os.path.join('..', database_name)  # Перемещение на 2 уровня вверх и указание имени файла

# Преобразование относительного пути в абсолютный
absolute_path = os.path.abspath(relative_path)

# Создание URL для подключения к базе данных SQLite
db_url = f'sqlite+aiosqlite:///{absolute_path}'

async_engine = create_async_engine(db_url, echo=True)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    is_blocked = Column(Boolean, nullable=False, default=False)

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True)
    text = Column(String)
    id_user = Column(ForeignKey("users.id"))

class Apartment(Base):
    __tablename__ = "apartments"

    id = Column(Integer, primary_key=True)
    apartment_num = Column(String, nullable=True)
    address_id = Column(ForeignKey("addresses.id"))
