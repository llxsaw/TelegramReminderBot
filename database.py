import sqlite3
import datetime


# Инициализация ДБ
def init_db():
    conn = sqlite3.connect('tasks.db')
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_text TEXT NOT NULL,
            notify_time TIMESTAMP NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
            -- 'pending' - ожидает, 'reminded' - напомнили за час, 'done' - выполнено
        )
    """)
    conn.commit()
    conn.close()

# Добавление задачи в базу
def add_task(user_id: int, task_text: str, notify_time: datetime.datetime):
    conn = sqlite3.connect('tasks.db')
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (user_id, task_text, notify_time) VALUES (?, ?, ?)",
        (user_id, task_text, notify_time)
    )
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return task_id

# Получение всех задач , которые еще не выполнены
def get_pending_tasks():
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks where status != 'done'")
    tasks = cur.fetchall()
    conn.close()
    return tasks


# Обновление статуса задачи
def update_task_status(task_id: int, status: str):
    conn = sqlite3.connect('tasks.db')
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET status = ? WHERE id = ?",
                (status, task_id))
    conn.commit()
    conn.close()

