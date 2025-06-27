import asyncio
import logging
import datetime
from time import timezone

from config import BOT_TOKEN

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command, StateFilter, state
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import database as db

BOT_TOKEN = BOT_TOKEN
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")


class AddTask(StatesGroup):
    waiting_for_task_text = State()
    waiting_for_time = State()


async def send_reminder(user_id: int, task_text: str, task_id: int):
    await bot.send_message(user_id,
                           f"🔔 НАПОМИНАНИЕ ЧЕРЕЗ 1 ЧАС 🔔\n\n"
                           f"📝 Задача: {task_text}"
    )
    db.update_task_status(task_id, 'reminded')


async def send_notification(user_id: int, task_text: str, task_id: int):
    await bot.send_message(
        user_id,
        f"⏰ ВРЕМЯ НАСТАЛО! ⏰\n\n"
        f"🚀 Пора выполнить задачу: {task_text}"
    )
    db.update_task_status(task_id, 'done')


@router.message(Command('start'))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я твой бот-планировщик.\n\n"
        "Я помогу тебе не забыть о важных делах.\n\n"
        "Чтобы добавить новую задачу, используй команду /addtask"
    )


@router.message(Command('addtask'))
async def cmd_addtask(message: Message, state: FSMContext):
    await state.set_state(AddTask.waiting_for_task_text)
    await message.answer("✏️ Введите текст вашей задачи:")


@router.message(StateFilter(AddTask.waiting_for_task_text))
async def process_task_text(message: Message, state: FSMContext):
    await state.update_data(task_text=message.text)
    await state.set_state(AddTask.waiting_for_time)
    await message.answer(
        "🗓️ Отлично\! Теперь введите дату и время для уведомления\n\n"
        "Формат: `ДД.ММ.ГГГГ ЧЧ:ММ`\n"
        "Например: `25.12.2025 15:30`",
        parse_mode="MarkdownV2"
    )


@router.message(StateFilter(AddTask.waiting_for_time))
async def process_time(message:Message, state: FSMContext):
    try:
        notify_time_str = message.text
        notify_time = datetime.datetime.strptime(notify_time_str, "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer("❌ Неверный формат. Пожалуйста, введите дату и время в формате `ДД.ММ.ГГГГ ЧЧ:ММ`:",
                             parse_mode="MarkdownV2")
        return

    if notify_time <= datetime.datetime.now():
        await message.answer("❌ Это время уже в прошлом! Пожалуйста, укажите будущее время.")
        return

    user_data = await state.get_data()
    task_text = user_data['task_text']
    user_id = message.from_user.id

    task_id = db.add_task(user_id, task_text, notify_time)

    scheduler.add_job(
        send_notification,
        'date',
        run_date=notify_time,
        args=[user_id, task_text, task_id],
        id=f"notification_{task_id}"
    )

    reminder_time = notify_time - datetime.timedelta(hours=1)
    if reminder_time > datetime.datetime.now():
        scheduler.add_job(
            send_reminder,
            'date',
            run_date=reminder_time,
            args=[user_id, task_text, task_id],
            id=f"reminder_{task_id}"
        )

    await message.answer(
        f"✅ Отлично! Задача '{task_text}' запланирована на {notify_time.strftime('%d.%m.%Y в %H:%M')}.\n\n"
        "Я пришлю уведомление вовремя и за час до этого (если возможно)"
    )

    await state.clear()


async def load_pending_tasks():
    logging.info("Loading pending tasks...")
    tasks = db.get_pending_tasks()
    now = datetime.datetime.now()

    for task in tasks:
        task_id = task['id']
        user_id = task['user_id']
        task_text = task['task_text']
        notify_time = datetime.datetime.fromisoformat(task['notify_time'])
        status = task['status']

        if notify_time <= now:
            db.update_task_status(task_id, 'done')
            continue

        scheduler.add_job(
            send_notification,
            'date',
            run_date=notify_time,
            args=[user_id, task_text, task_id],
            id=f"notification_{task_id}"
        )

        logging.info(f"Запланировано основное уведомление для задачи #{task_id} на {notify_time}")


        reminder_time = notify_time - datetime.timedelta(hours=1)
        if status == 'pending' and reminder_time > now:
            scheduler.add_job(
                send_notification,
                'date',
                run_date=reminder_time,
                args=(user_id, task_text, task_id),
                id=f"notification_{task_id}"
            )
            logging.info(f"Запланировано предварительное напоминание для задачи #{task_id} на {reminder_time}")


@router.message(Command('tasks'))
async def cmd_list_tasks(message: Message):
    rows = db.get_user_tasks(message.from_user.id)
    if not rows:
        return await message.answer('📭 У вас нет активных задач')

    buttons = []
    for t in rows:
        label = f"{t['task_text']} — {t['notify_time'][:16]}"
        buttons.append([
            InlineKeyboardButton(text="🔍 " + label, callback_data=f"view:{t['id']}"),
            InlineKeyboardButton(text="✅ Сделано", callback_data=f"done:{t['id']}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{t['id']}")
        ])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer("Вот Ваши задачи:", reply_markup=kb)
    return None


@router.callback_query(F.data == 'noop')
async def cb_noop(call: CallbackQuery):
    await call.answer()


@router.callback_query(F.data.startswith('done:'))
async def cb_done(call: CallbackQuery):
    task_id = int(call.data.split(':')[1])
    db.mark_task_done(task_id)
    await call.message.edit_text("✅ Задача отмечена как выполненная.")
    await call.answer("Отметил как готовое")


@router.callback_query(F.data.startswith('delete:'))
async def cb_delete(call: CallbackQuery):
    task_id = int(call.data.split(":")[1])
    await call.message.edit_text(
        "⚠️ Вы точно хотите удалить задачу?",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="Да, удалить", callback_data=f"confirm:delete:{task_id}"),
            InlineKeyboardButton(text="Нет", callback_data="noop"),
        )
    )


@router.callback_query(F.data.startswith('confirm_delete:'))
async def cb_confirm_delete(call: CallbackQuery):
    task_id = int(call.data.split(':')[1])
    db.delete_task(task_id)
    await call.message.edit_text("🗑 Задача удалена.")
    await call.answer("Удалено")


@router.callback_query(F.data.startswith('view:'))
async def cb_view(call: CallbackQuery):
    task_id = int(call.data.split(":")[1])
    row = next(r for r in db.get_user_tasks(call.from_user.id) if r ["id"] == task_id)
    text = (
        f"📝 <b>Задача</b>: {row['task_text']}\n"
        f"⏰ <b>Напоминание</b>: {row['notify_time']}\n"
        f"ℹ️ <b>Статус</b>: {row['status']}"
    )
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{task_id}"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="noop")
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()


async def main():
    db.init_db()
    scheduler.start()
    await load_pending_tasks()
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот Остановлен")

















