from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from sqlalchemy import func, select
from db import SessionLocal, Recipe


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
