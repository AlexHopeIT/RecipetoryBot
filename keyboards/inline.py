from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from db import Recipe


async def main_menu_keyboard(state: FSMContext):
    '''Создание инлайн-клавы главного меню'''
    builder = InlineKeyboardBuilder()

    builder.button(
        text='🔍 Найти рецепт',
        callback_data='find_recipe_inline'
        )
    builder.button(
        text='📜 Случайный рецепт',
        callback_data='random_recipe_inline'
        )
    builder.button(
        text='🥦 Поиск рецепта по ингредиентам',
        callback_data='by_ingredients_inline'
        )
    builder.button(
        text='⭐️ Избранное',
        callback_data='favorites_inline'
        )
    builder.button(
        text='🛒 Список покупок',
        callback_data='view_shopping_list'
        )

    builder.adjust(2, 1, 2)

    user_data = await state.get_data()
    last_recipe_id = user_data.get('last_recipe_id')

    if last_recipe_id:
        builder.button(
            text='🔙 Назад',
            callback_data=f'back_to_recipe:{last_recipe_id}'
            )
        builder.adjust(1, 2, 1, 2)

    return builder.as_markup()


def recipe_actions_keyboard(
        is_favorite: bool, recipe_id: int, page: int = None
        ):
    '''Инлайн-клава для действий с рецептом'''
    builder = InlineKeyboardBuilder()
    if is_favorite:
        builder.button(
            text='❌ Удалить из избранного',
            callback_data=f'remove_favorite:{recipe_id}'
        )
        builder.button(
            text='🛒 Добавить ингредиенты в список покупок',
            callback_data=f'add_to_shopping_list:{recipe_id}'
        )
    else:
        builder.button(
            text='💾 Добавить в избранное',
            callback_data=f'add_favorite:{recipe_id}'
        )

    if page is not None:
        builder.button(
            text='⬅️ Назад к списку',
            callback_data=f'favorites_page:{page}'
        )

    builder.button(
            text='Ⓜ️ Главное меню',
            callback_data='main_menu_inline'
        )

    builder.adjust(1)
    return builder.as_markup()


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
            callback_data=f'view_recipe:{recipe.id}:{page}'
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


async def shopping_list_actions_keyboard():
    builder = InlineKeyboardBuilder()

    builder.button(
        text='🗑️ Очистить весь список',
        callback_data='clear_shopping_list'
    )

    builder.button(
        text='⬅️ Главное меню',
        callback_data='main_menu_inline'
    )
