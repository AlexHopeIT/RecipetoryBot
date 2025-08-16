from aiogram import Router, types
from aiogram.client.bot import Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from sqlalchemy import func, select, or_
from sqlalchemy.orm import selectinload
from db import SessionLocal, Recipe, User
from .states import FindRecipeState, ByIngredientsState
from utils import (send_random_recipe, start_search_dialog,
                   process_search_query_and_display_results,
                   send_selected_recipe_by_choice,
                   start_by_ingredients_search,
                   process_search_by_ingredients, from_favorites,
                   send_one_recipe)
from keyboards.inline import main_menu_keyboard, recipe_actions_keyboard


user_handlers_router = Router()


@user_handlers_router.message(Command('random_recipe'))
async def random_recipe(message: types.Message,
                        state: FSMContext):
    '''Ручка для выдачи рандомного рецепта пользователю'''
    send_random_recipe(message, state)


@user_handlers_router.callback_query(
        lambda c: c.data == 'random_recipe_inline'
        )
async def random_recipe_inline(callback: types.CallbackQuery,
                               state: FSMContext):
    await callback.answer()
    await send_random_recipe(callback.message, state)


@user_handlers_router.message(Command('find_recipe'))
async def find_recipe(message: types.Message, state: FSMContext):
    '''Ручка для поиска рецепта по названию'''
    await start_search_dialog(message, state)


@user_handlers_router.callback_query(
        lambda c: c.data == 'find_recipe_inline'
        )
async def find_recipe_inline(callback: types.CallbackQuery,
                             state: FSMContext):
    await callback.answer()
    await start_search_dialog(callback.message, state)


@user_handlers_router.message(FindRecipeState.waiting_for_name)
async def process_recipe_name(message: types.Message, state: FSMContext):
    '''Первый шаг поиска. Подготовка списка найденных рецептов'''
    await process_search_query_and_display_results(message, state)


@user_handlers_router.message(FindRecipeState.waiting_for_choice)
async def process_recipe_choice(message: types.Message, state: FSMContext):
    '''Второй шаг поиска. Обработка выбора юзера'''
    await send_selected_recipe_by_choice(message, state)


@user_handlers_router.message(Command('by_ingredients'))
async def find_recipe_by_ingredients(message: types.Message, state: FSMContext):
    '''Ручка поиска по ингредиентам'''
    await start_by_ingredients_search(message, state)


@user_handlers_router.callback_query(
        lambda c: c.data == 'by_ingredients_inline'
        )
async def find_recipe_by_ingredients_inline(
    callback: types.CallbackQuery,
    state: FSMContext
):
    await callback.answer()
    await start_by_ingredients_search(callback.message, state)


@user_handlers_router.message(ByIngredientsState.waiting_for_ingredients)
async def process_recipe_ingredients(message: types.Message, state: FSMContext):
    '''Первый шаг поиска. Подготовка списка найденных рецептов'''
    await process_search_by_ingredients(message, state)


@user_handlers_router.message(ByIngredientsState.waiting_for_choice)
async def process_choice(message: types.Message, state: FSMContext):
    '''Второй шаг поиска. Обработка выбора юзера'''
    await send_selected_recipe_by_choice(message, state)


@user_handlers_router.callback_query(
    lambda c: c.data == 'main_menu_inline'
)
async def main_menu_inline(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    keyboard = await main_menu_keyboard(state)
    await callback.message.answer(
        'Вы вернулись в главное меню. Выберите действие:',
        reply_markup=keyboard
        )


@user_handlers_router.callback_query(
    lambda c: c.data == 'favorites_inline'
)
async def favorites_inline(callback: types.CallbackQuery, state: FSMContext):
    await from_favorites(callback, state)


@user_handlers_router.callback_query(
    lambda c: c.data.startswith('add_favorite:')
)
async def add_favorite(
    callback: types.CallbackQuery,
    state: FSMContext,
    bot: Bot
                       ):
    await callback.answer('Рецепт добавлен в избранное!')
    user_id = callback.from_user.id
    try:
        recipe_id = int(callback.data.split(':')[1])
    except (IndexError, ValueError):
        return
    async with SessionLocal() as db:
        user_result = await db.execute(
            select(User).options(
                selectinload(User.favorites_recipes)
                ).where(User.id == user_id)
        )
        recipe_result = await db.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )

        user = user_result.scalars().first()
        recipe = recipe_result.scalars().first()

        if user and recipe:
            if recipe not in user.favorites_recipes:
                user.favorites_recipes.append(recipe)
                await db.commit()
                await bot.edit_message_reply_markup(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    reply_markup=recipe_actions_keyboard(
                        is_favorite=True,
                        recipe_id=recipe_id
                        )
                    )


@user_handlers_router.callback_query(
    lambda c: c.data.startswith('remove_favorite:')
)
async def remove_favorite(
    callback: types.CallbackQuery,
    state: FSMContext,
    bot: Bot
                        ):
    await callback.answer(
                    'Рецепт удален из избранного!'
                )
    user_id = callback.from_user.id
    try:
        recipe_id = int(callback.data.split(':')[1])
    except (IndexError, ValueError):
        return
    async with SessionLocal() as db:
        user_result = await db.execute(
            select(User).options(
                selectinload(User.favorites_recipes)
                ).where(User.id == user_id)
        )
        recipe_result = await db.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )

        user = user_result.scalars().first()
        recipe = recipe_result.scalars().first()

        if user and recipe:
            if recipe in user.favorites_recipes:
                user.favorites_recipes.remove(recipe)
                await db.commit()
                await bot.edit_message_reply_markup(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    reply_markup=recipe_actions_keyboard(
                        is_favorite=False,
                        recipe_id=recipe_id
                        )
                    )


@user_handlers_router.callback_query(
    lambda c: c.data.startswith('back_to_recipe')
)
async def back_to_recipe(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    try:
        recipe_id = int(callback.data.split(':')[1])
    except (IndexError, ValueError):
        keyboard = await main_menu_keyboard(state)
        await callback.message.answer(
            'Ошибка при получении ID рецепта... Возвращаю в главное меню',
            reply_markup=keyboard
        )
        return

    async with SessionLocal() as db:
        result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
        found_recipe = result.scalars().first()

        if found_recipe:
            user_id = callback.from_user.id
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalars().first()
            is_favorite = found_recipe in user.favorites_recipes if user else False

            await send_one_recipe(
                callback.message, found_recipe, is_favorite, state
            )

            await state.clear()
        else:
            keyboard = await main_menu_keyboard(state)

            await callback.message.answer(
                'Произошла внутренняя ошибка...\n'
                'Возвращаю в главное меню...',
                reply_markup=keyboard
            )
