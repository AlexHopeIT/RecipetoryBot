'''
Файл для создания БД
'''

import os
from sqlalchemy import (Column, Integer,
                        String, Text, ForeignKey, Table)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship


DATABASE_NAME = 'recipes.db'
DATA_DIR = 'data'
DATABASE_URL = f'sqlite+aiosqlite:///{os.path.join(DATA_DIR, DATABASE_NAME)}'


os.makedirs(DATA_DIR, exist_ok=True)

engine = create_async_engine(DATABASE_URL, echo=True)

Base = declarative_base()


favorites_table = Table(
    'favorites', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('recipe_id', Integer, ForeignKey('recipes.id'))
)

shopping_recipes_table = Table(
    'shoping_recipes', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('recipe_id', Integer, ForeignKey('recipes.id'))
)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=False)
    username = Column(String(100), nullable=True)

    favorites_recipes = relationship(
        'Recipe',
        secondary=favorites_table,
        backref='faivorited_by'
    )

    shopping_list_items = relationship(
        'ShoppingList',
        backref='user',
        lazy='joined'
    )

    shoping_recipes = relationship(
        'Recipe',
        secondary=shopping_recipes_table,
        backref='in_shoping_list_for'
    )

    def __repr__(self):
        return f'<User(id={self.id}), username={self.username}'


class Recipe(Base):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    ingredients = Column(Text, nullable=False)
    instructions = Column(Text, nullable=False)
    image_url = Column(String(300), nullable=True)
    cuisine = Column(String(50), nullable=True)

    name_ru = Column(String(50), nullable=True)
    ingredients_ru = Column(Text, nullable=True)
    instructions_ru = Column(Text, nullable=True)

    def __repr__(self):
        return f'Recipe(name="{self.name}")'


class ShoppingList(Base):
    __tablename__ = 'shopping_list'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    item_name = Column(String(200), nullable=False)

    def __repr__(self):
        return f'<ShoppingList(user_id={self.user_id}), item_name="{self.item_name}">'


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False)


def get_db():
    '''Получение сессии БД'''
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == '__main__':
    import asyncio
    asyncio.run(create_tables())
    print('Таблица создана в файле recipes.db')
