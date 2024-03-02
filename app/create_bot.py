import os
from datetime import datetime

from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage


# BOT_TOKEN = ""

bot = Bot(token="7105917785:AAHmFFo0HYk7LpOMWD9BFVHhBwvwZ8wZc9A")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)