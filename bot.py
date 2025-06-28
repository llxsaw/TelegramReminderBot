# bot.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, TIMEZONE
from database.database import init_db
from handlers.add_task import router as add_router
from handlers.base import router as base_router
from handlers.edit_task import router as edit_router
from handlers.tasks import router as tasks_router
from scheduler.jobs import scheduler, load_pending_tasks


logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# include routers
dp.include_router(base_router)
dp.include_router(add_router)
dp.include_router(tasks_router)
dp.include_router(edit_router)


async def main():
    init_db()
    scheduler.start()
    await load_pending_tasks()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
