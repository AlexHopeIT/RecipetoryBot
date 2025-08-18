from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from db import Recipe


async def main_menu_keyboard(state: FSMContext):
    '''Создание инлайн-клавы главного меню'''
    find_button = InlineKeyboardButton(
        text='🔍 Найти рецепт',
        callback_data='find_recipe_inline'
        )
    random_button = InlineKeyboardButton(
        text='📜 Случайный рецепт',
        callback_data='random_recipe_inline'
        )
    by_ingredients = InlineKeyboardButton(
        text='🥦 Поиск рецепта по ингредиентам',
        callback_data='by_ingredients_inline'
    )

    favorites = InlineKeyboardButton(
        text='⭐️ Избранное',
        callback_data='favorites_inline'
    )

    keyboard_rows = [
        [find_button, random_button],
        [by_ingredients],
        [favorites]
    ]

    user_data = await state.get_data()
    last_recipe_id = user_data.get('last_recipe_id')

    if last_recipe_id:
        back_to_recipe_button = InlineKeyboardButton(
            text='🔙 Назад',
            callback_data=f'back_to_recipe:{last_recipe_id}'
        )

        keyboard_rows.insert(0, [back_to_recipe_button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


def recipe_actions_keyboard(is_favorite: bool, recipe_id: int):
    '''Инлайн-клава для действий с рецептом'''
    if is_favorite:
        button = InlineKeyboardButton(
            text='❌ Удалить из избранного',
            callback_data=f'remove_favorite:{recipe_id}'
        )
    else:
        button = InlineKeyboardButton(
            text='💾 Добавить в избранное',
            callback_data=f'add_favorite:{recipe_id}'
        )

    main_menu_button = InlineKeyboardButton(
            text='Ⓜ️ Главное меню',
            callback_data='main_menu_inline'
        )

    return InlineKeyboardMarkup(inline_keyboard=[
        [button],
        [main_menu_button]
    ])


async def favorites_paginated_keyboard(
        recipes: list[Recipe], page: int, per_page: int = 5
        ):
    builder = InlineKeyboardBuilder()

    start_index = page * per_page
    end_index = start_index + per_page
    current_recipes = recipes[start_index:end_index]

    for recipe in current_recipes:
        builder.button(
            text=recipe.name_ru,
            callback_data=f'view_recipe:{recipe.id}'
        )

    builder.adjust(1)

    nav_buttons = []

    next_page_number = page + 1
    previous_page_number = page - 1

    if end_index < len(recipes): 
        nav_buttons.append(InlineKeyboardButton(
            text='Далее➡️',
            callback_data=f'favorites_page:{next_page_number}'
            )
        )

    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text='Назад⬅️',
            callback_data=f'favorites_page:{previous_page_number}'
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.button(
        text='⬅️ Главное меню', callback_data='main_menu_inline'
        )

    return builder.as_markup()
