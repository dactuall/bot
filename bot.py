import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())  # указываем storage для FSM

# Определяем состояния
class Form(StatesGroup):
    name = State()
    age = State()

@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Привет! Как тебя зовут?")
    await state.set_state(Form.name)

@dp.message()
async def process_name(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == Form.name.state:
        await state.update_data(name=message.text)
        await message.answer("Сколько тебе лет?")
        await state.set_state(Form.age)
    elif current_state == Form.age.state:
        await state.update_data(age=message.text)
        data = await state.get_data()
        await message.answer(f"Имя: {data['name']}, возраст: {data['age']}")
        await state.clear()

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
