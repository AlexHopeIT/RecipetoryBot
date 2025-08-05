from aiogram import Router, types
from aiogram.filters import CommandStart, Command


common_router = Router()


@common_router.message(CommandStart)
async def cmd_start(message: types.Message):
    await message.answer(
        f'Привет, {message.from_user.first_name}!👋\n'
        'Я - Рецепторий, твой персональный кулинарный помощник! 🧑‍🍳\n'
        'Пиши /help, чтобы узнать, что я умею '
    )


@common_router.message(Command('help'))
async def cmd_help(message: types.Message):
    await message.answer(
        "Вот что я умею: 😉\n\n"
        "📜 /random_recipe - получить случайный рецепт\n"
        "🔍 /find_recipe - найти рецепт по названию\n"
        "🥦 /by_ingredients - найти рецепт по имеющимся ингредиентам\n"
        "⭐️ /favorites - показать твои любимые рецепты\n"
        "🛒 /shopping_list - составить список покупок"
    )