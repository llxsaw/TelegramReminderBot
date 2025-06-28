# scheduler/jobs.py
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from config import BOT_TOKEN
import database.database as db

bot = Bot(token=BOT_TOKEN)

scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")


async def send_reminder(user_id: int, task_text: str, task_id: int):
    await bot.send_message(
        user_id,
        f"🔔 НАПОМИНАНИЕ ЧЕРЕЗ 1 ЧАС 🔔\n\n"
        f"📝 Задача: {task_text}"
    )
    db.update_task_status(task_id, "reminded")


async def send_notification(user_id: int, task_text: str, task_id: int):
    await bot.send_message(
        user_id,
        f"⏰ ВРЕМЯ НАСТАЛО! ⏰\n\n"
        f"🚀 Пора выполнить задачу: {task_text}"
    )
    db.update_task_status(task_id, "done")


async def load_pending_tasks():
    now = datetime.datetime.now()
    for t in db.get_pending_tasks():
        notify_time = datetime.datetime.fromisoformat(t["notify_time"])
        if notify_time <= now:
            db.update_task_status(t["id"], "done")
            continue

        scheduler.add_job(
            send_notification,
            "date",
            run_date=notify_time,
            args=[t["user_id"], t["task_text"], t["id"]],
            id=f"notification_{t['id']}"
        )

        rem = notify_time - datetime.timedelta(hours=1)
        if t["status"] == "pending" and rem > now:
            scheduler.add_job(
                send_reminder,
                "date",
                run_date=rem,
                args=[t["user_id"], t["task_text"], t["id"]],
                id=f"reminder_{t['id']}"
            )
