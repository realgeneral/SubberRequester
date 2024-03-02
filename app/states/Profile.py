from aiogram.dispatcher.filters.state import State, StatesGroup


class Profile(StatesGroup):
    get_token = State()
    send_req = State()
