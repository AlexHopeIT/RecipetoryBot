from aiogram import types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from sqlalchemy import func, select, or_
from db import SessionLocal, Recipe
from handlers.states import FindRecipeState, ByIngredientsState
from keyboards.inline import main_menu_keyboard


async def send_one_recipe(
        event: types.Message | types.CallbackQuery,
        recipe: Recipe
        ):
    '''Отправляет один рецепт пользователю, включая фото и полный текст'''
    keyboard = main_menu_keyboard()

    caption_text = (
            f'<b>Рецепт:</b> {recipe.name_ru}'
        )
    full_recipe_text = (
        '<b>Ингредиенты:</b>'
        f'{recipe.ingredients_ru}\n\n'
        '<b>Инструкция по приготовлению:</b>'
        f'{recipe.instructions_ru}'
    )

    if recipe.image_url:
        await event.answer_photo(
            photo=recipe.image_url,
            caption=caption_text,
            parse_mode=ParseMode.HTML
        )
    else:
        await event.answer(caption_text, parse_mode=ParseMode.HTML,
                           reply_markup=keyboard)
    await event.answer(full_recipe_text, parse_mode=ParseMode.HTML,
                       reply_markup=keyboard)


async def send_random_recipe(event: types.Message | types.CallbackQuery):
    '''Получает случайный рецепт из БД и вызывает send_one_recipe'''
    async with SessionLocal() as db:
        result = await db.execute(select(Recipe).order_by(func.random()).limit(1))
        rand_recipe = result.scalars().first()

        if not rand_recipe:
            await event.answer('''К сожалению, я пока не знаю рецептов,
                                но уже активно изучаю кулинарную книгу''')
            return
        await send_one_recipe(event, rand_recipe)


async def start_search_dialog(
        event: types.Message | types.CallbackQuery,
        state: FSMContext
        ):
    '''Запуск диалога поиска рецепта'''
    await event.answer(
        'Введите название блюда, рецепт которого хотите найти'
        )
    await state.set_state(FindRecipeState.waiting_for_name)


async def process_search_query_and_display_results(
        message: types.Message, state: FSMContext
        ):
    async with SessionLocal() as db:
        search_query = message.text
        await message.answer(f'Ищу рецепт: "{search_query}"...')

        result = await db.execute(
            select(Recipe)
            .where(
                or_(
                    Recipe.name.like(f'%{search_query}%'),
                    Recipe.name_ru.like(f'%{search_query}%')
                )
            )
        )

        found_recipes = result.scalars().all()

        if found_recipes:
            answ = ['Найдены следующие рецепты:']
            for i, recipe in enumerate(found_recipes, start=1):
                answ.append(f'{i}. {recipe.name_ru}')

            final_message = '\n'.join(answ)

            await message.answer(final_message)
            await message.answer(
                'Напишите номер блюда, рецепт которого хотите получить🍽'
                )

            await state.update_data(found_recipes=found_recipes)
            await state.set_state(FindRecipeState.waiting_for_choice)
        else:
            await message.answer('Рецептов с таким названием не найдено 🤷‍♂️')
            await state.clear()


async def send_selected_recipe_by_choice(
        message: types.Message, state: FSMContext
        ):
    '''Принимает выбор блюда юзера из списка и отправляет рецепт'''
    user_data = await state.get_data()
    found_recipes = user_data.get('found_recipes')

    if not found_recipes:
        await message.answer(
            'Произошла ошибка... Попробуйте снова начать поиск рецепта...'
        )
        await state.clear()
        return

    try:
        choice = int(message.text)
        if 1 <= choice <= len(found_recipes):
            selected_recipe = found_recipes[choice - 1]

            await send_one_recipe(message, selected_recipe)
            await state.clear()
        else:
            await message.answer('Введите корректный номер рецепта из списка.')
    except ValueError:
        await message.answer('Введите число!')


async def start_by_ingredients_search(
        event: types.Message | types.CallbackQuery,
        state: FSMContext
        ):
    '''Запуск диалога поиска по ингредиентам'''
    await event.answer(
        'Введите ингредиенты, которые у вас есть, через запятую'
    )
    await state.set_state(ByIngredientsState.waiting_for_ingredients)


async def process_search_by_ingredients(
        message: types.Message, state: FSMContext
        ):
    keyboard = main_menu_keyboard()
    async with SessionLocal() as db:
        ingredients = message.text
        ingredients_list = [item.strip() for item in ingredients.split(',')]

        search_conditions = []
        for ingredient in ingredients_list:
            search_conditions.append(
                Recipe.ingredients_ru.ilike(f'%{ingredient}%')
                )
        result = await db.execute(
            select(Recipe).where(or_(*search_conditions))
            )

        found_recipes = result.scalars().all()
        if found_recipes:
            answ = ['Найдены следующие рецепты:']
            for i, recipe in enumerate(found_recipes, start=1):
                answ.append(f'{i}. {recipe.name_ru}')

            final_message = '\n'.join(answ)

            await message.answer(final_message)
            await message.answer(
                'Напишите номер блюда, рецепт которого хотите получить🍽'
                )

            await state.update_data(found_recipes=found_recipes)
            await state.set_state(ByIngredientsState.waiting_for_choice)
        else:
            await message.answer('Рецептов не найдено 🤷‍♂️',
                                 reply_markup=keyboard)
            await state.clear()
