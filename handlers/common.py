from aiogram import Router, types
from aiogram.filters import CommandStart


common_router = Router()


@common_router.message(CommandStart)
async def cmd_start(message: types.Message):
    await message.answer(
        f'Привет, {message.from_user.first_name}!👋\n'
        'Я - Рецепторий, твой персональный кулинарный помощник! 🧑‍🍳\n'
        'Пиши /help, чтобы узнать, что я умею '
    )
