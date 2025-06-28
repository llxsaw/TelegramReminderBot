from aiogram.fsm.state import StatesGroup, State


class AddTask(StatesGroup):
    waiting_for_task_text = State()
    waiting_for_time = State()


class EditTask(StatesGroup):
    waiting_for_new_text = State()
    waiting_for_new_time = State()
