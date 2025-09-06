import re
from aiogram import types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from sqlalchemy import func, select, or_, and_
from sqlalchemy.orm import selectinload
from db import SessionLocal, Recipe, User, favorites_table as favorites
from handlers.states import FindRecipeState, ByIngredientsState
from keyboards.inline import (
    main_menu_keyboard, recipe_actions_keyboard, favorites_paginated_keyboard
    )


async def send_one_recipe(
        event: types.Message | types.CallbackQuery,
        recipe: Recipe, is_favorite: bool, state: FSMContext,
        page: int = None
        ):
    '''Отправляет один рецепт пользователю, включая фото и полный текст'''
    keyboard = recipe_actions_keyboard(is_favorite, recipe.id)

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


async def send_random_recipe(event: types.Message | types.CallbackQuery,
                             state: FSMContext):
    '''Получает случайный рецепт из БД и вызывает send_one_recipe'''
    is_favorite = False
    async with SessionLocal() as db:
        result = await db.execute(select(Recipe).order_by(func.random()).limit(1))
        rand_recipe = result.scalars().first()

        if not rand_recipe:
            await event.answer('''К сожалению, я пока не знаю рецептов,
                                но уже активно изучаю кулинарную книгу''')
            return
        await send_one_recipe(event, rand_recipe, is_favorite, state)


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
            user_id = message.from_user.id
            recipe_id = selected_recipe.id
            
            async with SessionLocal() as db:
                # Проверяем, является ли рецепт избранным
                is_favorite_check = await db.execute(
                    select(favorites).where(
                        and_(
                            favorites.c.user_id == user_id,
                            favorites.c.recipe_id == recipe_id
                        )
                    )
                )
                is_favorite = is_favorite_check.first() is not None

            # Исправленный вызов функции
            await send_one_recipe(message, selected_recipe, is_favorite, state)
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
    keyboard = main_menu_keyboard(state)
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


async def from_favorites(callback: types.CallbackQuery, state: FSMContext):
    '''Получает и выводит юзеру список избранных рецептов'''
    await callback.answer()

    async with SessionLocal() as db:
        user_id = callback.from_user.id
        result = await db.execute(
            select(User).options(
                selectinload(User.favorites_recipes)
                ).where(User.id == user_id)
            )
        user = result.scalars().first()

        if user and user.favorites_recipes:
            keyboard = await favorites_paginated_keyboard(
                user.favorites_recipes,
                page=0
            )
            await callback.message.answer(
                '⭐️ Ваши избранные рецепты:\n'
                'Выберите, чтобы просмотреть рецепт:',
                reply_markup=keyboard
                )
        else:
            keyboard = await main_menu_keyboard(state)
            await callback.message.answer(
                'У вас пока нет избранных рецептов 🤷‍♂️',
                reply_markup=keyboard
            )
