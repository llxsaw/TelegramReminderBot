# handlers/edit_task.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from states import EditTask
from database.database import update_task_text_and_time
import datetime

router = Router()


@router.callback_query(F.data.startswith("edit:"))
async def cb_start_edit(call: CallbackQuery, state: FSMContext):
    task_id = int(call.data.split(":")[1])
    await state.update_data(task_id=task_id)
    await state.set_state(EditTask.waiting_for_new_text)
    await call.message.edit_text("✏️ Новый текст задачи:")


@router.message(StateFilter(EditTask.waiting_for_new_text))
async def process_new_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(EditTask.waiting_for_new_time)
    await message.answer("🗓 Новый дата и время (ДД.MM.YYYY HH:MM):")


@router.message(StateFilter(EditTask.waiting_for_new_time))
async def process_new_time(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        dt = datetime.datetime.strptime(message.text, "%d.%m.%Y %H:%M")
    except ValueError:
        return await message.answer("❌ Неверный формат.")
    update_task_text_and_time(data["task_id"], data["text"], dt)
    await message.answer("✅ Задача обновлена!")
    await state.clear()
