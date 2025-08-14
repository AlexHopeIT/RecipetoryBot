from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from keyboards.inline import main_menu_keyboard
from db import SessionLocal, User


common_router = Router()


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


@common_router.message(CommandStart)
async def cmd_start(message: types.Message, state: FSMContext):
    keyboard = await main_menu_keyboard(state)
    async with SessionLocal() as db:
        user_id = message.from_user.id
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if not user:
            new_user = User(
                user_id=user_id,
                username=message.from_user.username
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)

    await message.answer(
        f'Привет, {message.from_user.first_name}!👋\n'
        'Я - Рецепторий, твой персональный кулинарный помощник! 🧑‍🍳\n'
        'Пиши /help, чтобы узнать, что я умею ',
        reply_markup=keyboard
    )
