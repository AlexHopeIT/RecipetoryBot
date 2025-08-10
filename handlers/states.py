from aiogram.fsm.state import State, StatesGroup


class FindRecipeState(StatesGroup):
    waiting_for_name = State()
    waiting_for_choice = State()