
````markdown
# Telegram Reminder Bot 🕒

Простой Telegram-бот для создания напоминаний о задачах. Пользователи могут добавлять задачи с помощью команды `/addtask`, и бот пришлёт уведомление:

- За 1 час до события
- В момент события

⚙️ Возможности

- Команда /addtask — добавить задачу с текстом и датой/временем
- Уведомления за 1 час и в момент задачи
- Локальное хранение задач в базе данных task.db
- Простое и быстрое использование

🛠 Используемые технологии

- Python 3.10+
- [Aiogram](https://github.com/aiogram/aiogram) (Telegram Bot API)
- SQLite (локальная база данных)

🚀 Запуск

1. Установи зависимости:


pip install -r requirements.txt
````

2. Создай файл `config.py` со следующим содержимым:

```python
TOKEN = "твой_telegram_token"
```

3. Запусти бота:

```bash
python main.py
```

## 📌 Пример использования

```plaintext
/addtask Купить продукты завтра в 19:00
```

Бот напомнит тебе в 18:00 и в 19:00.


---

## Контакты / Contacts 📞
- Telegram: @llxsaw
- Instagram: l1xsaww
- Email: holynskyiartem.work@gmail.com

