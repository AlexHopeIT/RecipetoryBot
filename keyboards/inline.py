from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard():
    '''Создание инлайн-клавы главного меню'''
    find_button = InlineKeyboardButton(text='🔍 Найти рецепт', callback_data='find_recipe_inline')
    random_button = InlineKeyboardButton(text='📜 Случайный рецепт', callback_data='random_recipe_inline')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [find_button], [random_button],
    ])
    return keyboard