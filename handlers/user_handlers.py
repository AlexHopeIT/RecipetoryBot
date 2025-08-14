from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from sqlalchemy import func, select, or_
from db import SessionLocal, Recipe
from .states import FindRecipeState, ByIngredientsState
from utils import (send_random_recipe, start_search_dialog,
                   process_search_query_and_display_results,
                   send_selected_recipe_by_choice,
                   start_by_ingredients_search,
                   process_search_by_ingredients, from_favorites)
from keyboards.inline import main_menu_keyboard


user_handlers_router = Router()


@user_handlers_router.message(Command('random_recipe'))
async def random_recipe(message: types.Message):
    '''Ручка для выдачи рандомного рецепта пользователю'''
    send_random_recipe(message)


@user_handlers_router.callback_query(
        lambda c: c.data == 'random_recipe_inline'
        )
async def random_recipe_inline(callback: types.CallbackQuery):
    await callback.answer()
    await send_random_recipe(callback.message)


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
    await callback.answer()
    await from_favorites(callback, state)
    

# РЕАЛИЗОВАТЬ:
@user_handlers_router.callback_query(
    lambda c: c.data == 'add_favorite:RECIPE_ID'
)


@user_handlers_router.callback_query(
    lambda c: c.data == 'remove_favorite:RECIPE_ID'
)


@user_handlers_router.callback_query(
    lambda c: c.data == 'back_to_recipe:RECIPE_ID'
)