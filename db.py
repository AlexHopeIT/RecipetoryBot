'''
Файл для создания БД
'''

import os
from sqlalchemy import (create_engine, Column, Integer,
                        String, Text)
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_NAME = 'recipes.db'
DATA_DIR = 'data'
DATABASE_URL = f'sqlite:///{os.path.join(DATA_DIR, DATABASE_NAME)}'


os.makedirs(DATA_DIR, exist_ok=True)

engine = create_engine(DATABASE_URL)

Base = declarative_base()


class Recipe(Base):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    ingredients = Column(Text, nullable=False)
    instructions = Column(Text, nullable=False)
    image_url = Column(String(300), nullable=True)

    def __repr__(self):
        return f'Recipe(name="{self.name}")'


def create_tables():
    Base.metadata.create_all(engine)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    '''Получение сессии БД'''
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == '__main__':
    create_tables()
    print('Таблица создана в файле recipes.db')
