'''
Интеграция с API, наполнение БД
'''


import requests
import time
from googletrans import Translator
from sqlalchemy.exc import IntegrityError
from db import SessionLocal, Recipe


API_URL_BY_LETTER = 'https://www.themealdb.com/api/json/v1/1/search.php?f='

LETTERS = 'abcdefghijklmnopqrstuvwxyz'

translator = Translator()


def get_recipes_by_letter(letter):
    '''
    Делает запрос к API по заданной букве и возвращает список рецептов
    '''
    url = f'{API_URL_BY_LETTER}{letter}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get('meals') is not None:
            return data['meals']
        else:
            return []
    except requests.exceptions.RequestException as e:
        print(f'Ошибка при запросе к API для буквы "{letter}": {e}')
        return []


def translate_text(text):
    '''Перевод текста на русский язык'''
    if not text:
        return ''
    try:
        return translator.translate(text, src='en', dest='ru').text
    except Exception as e:
        print(f'Ошибка перевода: {e}')
        return ''


def fill_database():
    '''Наполнение БД'''
    db = SessionLocal()
    recipes_added = 0

    print('Start parsing')

    for letter in LETTERS:
        print(f'Загрузка рецептов на букву {letter}')
        recipes = get_recipes_by_letter(letter)

        if not recipes:
            continue

        for recipe_data in recipes:
            if not isinstance(recipe_data, dict):
                print(f'Пропускаем некорректные данные для буквы {letter}: {recipe_data}')
                continue
            try:
                ingredients_list = []
                for i in range(1, 21):
                    ingredient = recipe_data.get(f'strIngredient{i}')
                    measure = recipe_data.get(f'strMeasure{i}')
                    if ingredient and ingredient.strip():
                        ingredients_list.append(f'{ingredient.strip()} ({measure.strip()})')

                name_en = recipe_data.get('strMeal')
                ingredients_en = '\n'.join(ingredients_list)
                instructions_en = recipe_data.get('strInstructions')
                cuisine_en = recipe_data.get('strArea')

                if not name_en:
                    print('Пропуск рецепта без названия')
                    continue

                print(f'Переводим рецепт {name_en}')

                name_ru = translate_text(name_en)
                ingredients_ru = translate_text(ingredients_en)
                instructions_ru = translate_text(instructions_en)
                cuisine_ru = translate_text(cuisine_en)

                db_recipe = Recipe(
                    name=name_en,
                    ingredients=ingredients_en,
                    instructions=instructions_en,
                    image_url=recipe_data.get('strMealThumb'),
                    cuisine=cuisine_en,
                    name_ru=name_ru,
                    ingredients_ru=ingredients_ru,
                    instructions_ru=instructions_ru
                )

                db.add(db_recipe)
                db.commit()
                recipes_added += 1
            except IntegrityError:
                db.rollback()
                print(
                    f'Рецепт {recipe_data.get("strMeal")} уже есть в БД. Пропускаем'
                    )
            except Exception as e:
                db.rollback()
                print(f'Ошибка при добавлении рецепта: {e}')

        time.sleep(1)
    print(f'БД заполнена, добавлено {recipes_added} новых рецептов')
    db.close()


if __name__ == '__main__':
    fill_database()
