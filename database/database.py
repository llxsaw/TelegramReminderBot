import sqlite3
import datetime


# Инициализация ДБ
def init_db():
    conn = sqlite3.connect('../tasks.db')
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
    conn = sqlite3.connect('../tasks.db')
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
    conn = sqlite3.connect('../tasks.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks where status != 'done'")
    tasks = cur.fetchall()
    conn.close()
    return tasks


# Обновление статуса задачи
def update_task_status(task_id: int, status: str):
    conn = sqlite3.connect('../tasks.db')
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET status = ? WHERE id = ?",
                (status, task_id))
    conn.commit()
    conn.close()


def get_user_tasks(user_id: int):
    """
        Return all non-done tasks for user
    """
    conn = sqlite3.connect('../tasks.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM tasks
        WHERE user_id = ? AND status != 'done' 
        ORDER BY notify_time 
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_task(task_id: int):
    """Permanently remove task from list"""
    conn = sqlite3.connect('../tasks.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def mark_task_done(task_id: int):
    update_task_status(task_id, status='done')


def update_task_text_and_time(task_id: int, new_text: str, new_time: datetime.datetime):
    conn = sqlite3.connect('../tasks.db')
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET task_text = ?, notify_time = ?, status = 'pending' WHERE id = ?",
        (new_text, new_time, task_id)
    )
    conn.commit()
    conn.close()