# handlers/tasks.py

import datetime

from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.filters import Command

import database.database as db
from scheduler.jobs import scheduler

router = Router()


async def build_tasks_keyboard(user_id: int) -> InlineKeyboardMarkup:
    rows = db.get_user_tasks(user_id)
    if not rows:
        return None  # caller handles “no tasks” case

    kb_rows = []
    for t in rows:
        # 1️⃣ label with text + time
        label = f"{t['task_text']} — {t['notify_time'][:16]}"

        # 2️⃣ each row: [ view_button, done_button, delete_button ]
        kb_rows.append([
            InlineKeyboardButton(text=f"🔍 {label}", callback_data=f"view:{t['id']}"),
        ])

        kb_rows.append([
            InlineKeyboardButton(text="✅", callback_data=f"done:{t['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete:{t['id']}"),
        ])

    return InlineKeyboardMarkup(inline_keyboard=kb_rows)


@router.message(Command("tasks"))
async def cmd_list_tasks(message: Message) -> None:
    kb = await build_tasks_keyboard(message.from_user.id)
    if not kb:
        await message.answer("📭 У вас нет активных задач.")
        return

    await message.answer("📋 Ваши задачи:", reply_markup=kb)


@router.callback_query(F.data == "noop")
async def cb_go_back(call: CallbackQuery) -> None:
    # regenerate & edit in-place
    kb = await build_tasks_keyboard(call.from_user.id)
    if not kb:
        await call.message.edit_text("📭 У вас нет активных задач.")
        await call.answer()
        return

    await call.message.edit_text("📋 Ваши задачи:", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("view:"))
async def cb_view(call: CallbackQuery) -> None:
    task_id = int(call.data.split(":", 1)[1])
    row = next((r for r in db.get_user_tasks(call.from_user.id) if r["id"] == task_id), None)

    if not row:
        await call.message.edit_text("❌ Задача не найдена.")
        await call.answer()
        return

    text = (
        f"📝 <b>Задача</b>: {row['task_text']}\n"
        f"⏰ <b>Напоминание</b>: {row['notify_time']}\n"
        f"ℹ️ <b>Статус</b>: {row['status']}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{task_id}")],
        [InlineKeyboardButton(text="🔙 Назад",        callback_data="noop")],
    ])
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("done:"))
async def cb_done(call: CallbackQuery) -> None:
    task_id = int(call.data.split(":", 1)[1])
    db.mark_task_done(task_id)

    # cancel scheduled jobs if any
    for jid in (f"notification_{task_id}", f"reminder_{task_id}"):
        scheduler.remove_job(jid, jobstore=None, remove_all_jobs=False)

    await call.message.edit_text("✅ Задача отмечена как выполненная.")
    await call.answer("Отмечено сделано")


@router.callback_query(F.data.startswith("delete:"))
async def cb_delete(call: CallbackQuery) -> None:
    task_id = int(call.data.split(":", 1)[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Да, удалить", callback_data=f"confirm_delete:{task_id}"),
        InlineKeyboardButton(text="Нет",         callback_data="noop"),
    ]])
    await call.message.edit_text("⚠️ Вы точно хотите удалить задачу?", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("confirm_delete:"))
async def cb_confirm_delete(call: CallbackQuery) -> None:
    task_id = int(call.data.split(":", 1)[1])
    db.delete_task(task_id)

    # cancel scheduled jobs if any
    for jid in (f"notification_{task_id}", f"reminder_{task_id}"):
        scheduler.remove_job(jid, jobstore=None, remove_all_jobs=False)

    await call.message.edit_text("🗑 Задача удалена.")
    await call.answer("Удалено")
