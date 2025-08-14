from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext


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
