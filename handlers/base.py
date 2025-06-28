# handlers/base.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("start", "help"))
async def cmd_start(message: Message):
    await message.answer(
      "👋 Привет! Я бот-напоминалка.\n"
      "Добавить новую задачу: /addtask\n"
      "Список задач:          /tasks"
    )
