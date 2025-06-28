

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
import datetime

from database.database import add_task
from states import AddTask
from scheduler.jobs import scheduler, send_notification, send_reminder

router = Router()


@router.message(Command("addtask"))
async def cmd_addtask(message: Message, state: FSMContext):
    # 1) Ask for task text
    await state.set_state(AddTask.waiting_for_task_text)
    await message.answer("✏️ Введите текст задачи:")


@router.message(StateFilter(AddTask.waiting_for_task_text))
async def process_task_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(AddTask.waiting_for_time)
    await message.answer("🗓 Введите дату и время (ДД.MM.YYYY HH:MM):")


@router.message(StateFilter(AddTask.waiting_for_time))
async def process_time(message: Message, state: FSMContext):
    data = await state.get_data()

    # 2) Parse & validate
    try:
        notify_time = datetime.datetime.strptime(message.text, "%d.%m.%Y %H:%M")
    except ValueError:
        return await message.answer("❌ Неверный формат, повторите ввод.")
    if notify_time <= datetime.datetime.now():
        return await message.answer("❌ Укажите будущее время, пожалуйста.")

    # 3) Save to DB
    task_id = add_task(message.from_user.id, data["text"], notify_time)

    scheduler.add_job(
        send_notification,
        trigger="date",
        run_date=notify_time,
        args=[message.from_user.id, data["text"], task_id],
        id=f"notification_{task_id}"
    )

    reminder_time = notify_time - datetime.timedelta(hours=1)
    if reminder_time > datetime.datetime.now():
        scheduler.add_job(
            send_reminder,
            trigger="date",
            run_date=reminder_time,
            args=[message.from_user.id, data["text"], task_id],
            id=f"reminder_{task_id}"
        )

    # 4) Confirm to user & clear state
    await message.answer("✅ Задача запланирована!")
    await state.clear()
