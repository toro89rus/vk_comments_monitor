from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    reviewing_applications = State()
