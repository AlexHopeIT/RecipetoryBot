from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from sqlalchemy import func, select, or_
from db import SessionLocal, Recipe
from .states import FindRecipeState


user_handlers_router = Router()


@user_handlers_router.message(Command('random_recipe'))
async def random_recipe(message: types.Message):
    '''Ручка для выдачи рандомного рецепта пользователю'''
    async with SessionLocal() as db:
        result = await db.execute(select(Recipe).order_by(func.random()).limit(1))
        rand_recipe = result.scalars().first()

        if not rand_recipe:
            await message.answer('''К сожалению, я пока не знаю рецептов,
                                но уже активно изучаю кулинарную книгу''')
        caption_text = (
            f'<b>Случайный рецепт:</b> {rand_recipe.name_ru}'
        )
        full_recipe_text = (
            '<b>Ингредиенты:</b>'
            f'{rand_recipe.ingredients_ru}\n\n'
            '<b>Инструкция по приготовлению:</b>'
            f'{rand_recipe.instructions_ru}'
        )

        if rand_recipe.image_url:
            await message.answer_photo(
                photo=rand_recipe.image_url,
                caption=caption_text,
                parse_mode=ParseMode.HTML
            )
        else:
            await message.answer(caption_text, parse_mode=ParseMode.HTML)
        await message.answer(full_recipe_text, parse_mode=ParseMode.HTML)


@user_handlers_router.message(Command('find_recipe'))
async def find_recipe(message: types.Message, state: FSMContext):
    '''Ручка для поиска рецепта по названию'''
    await message.answer(
        'Введите название блюда, рецепт которого хотите найти'
        )
    await state.set_state(FindRecipeState.waiting_for_name)


@user_handlers_router.message(FindRecipeState.waiting_for_name)
async def process_recipe_name(message: types.Message, state: FSMContext):
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
                'Напишите число блюда, рецепт которого хотите получить🍽'
                )

            await state.update_data(found_recipes=found_recipes)
            await state.set_state(FindRecipeState.waiting_for_choice)
        else:
            await message.answer('Рецептов с таким названием не найдено 🤷‍♂️')
            await state.clear()


@user_handlers_router.message(FindRecipeState.waiting_for_choice)
async def process_recipe_choice(message: types.Message, state: FSMContext):
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

            caption_text = f'<b>Вы выбрали:</b> {selected_recipe.name_ru}'
            full_recipe_text = (
                '<b>Ингредиенты:</b>\n'
                f'{selected_recipe.ingredients_ru}\n\n'
                '<b>Инструкция:</b>\n'
                f'{selected_recipe.instructions_ru}'
            )

            if selected_recipe.image_url:
                await message.answer_photo(
                    photo=selected_recipe.image_url,
                    caption=caption_text,
                    parse_mode=ParseMode.HTML
                )
                await message.answer(
                    full_recipe_text,
                    parse_mode=ParseMode.HTML
                    )
            else:
                await message.answer(
                    f'{caption_text}\n\n{full_recipe_text}',
                    parse_mode=ParseMode.HTML
                )
            await state.clear()
        else:
            await message.answer('Введите корректный номер рецепта из списка.')
    except ValueError:
        await message.answer('Введите число!')
