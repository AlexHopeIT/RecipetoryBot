import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from db import create_tables
from handlers.common import common_router
from handlers.user_handlers import user_handlers_router


logging.basicConfig(level=logging.INFO)


async def main():
    await create_tables()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(user_handlers_router)
    dp.include_router(common_router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
