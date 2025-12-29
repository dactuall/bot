from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import sqlite3

# ==== НАСТРОЙКИ ====
TOKEN = "8568726318:AAGRTPevSPTEWPAAKuiidIGLdMwcBIT1XyY"
ADMIN_ID = 423805945  # сюда свой Telegram ID

# ==== БОТ И FSM ====
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ==== БАЗА ДАННЫХ ====
db = sqlite3.connect("profiles.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age TEXT,
    city TEXT,
    about TEXT,
    photo_id TEXT
)
""")
db.commit()

try:
    cursor.execute("ALTER TABLE profiles ADD COLUMN photo_id TEXT")
    db.commit()
except:
    pass

# ==== FSM СОСТОЯНИЯ ====
class AddProfile(StatesGroup):
    name = State()
    age = State()
    city = State()
    about = State()
    photo = State()

# ==== КНОПКА АДМИНКИ ====
admin_kb = ReplyKeyboardMarkup(resize_keyboard=True)
admin_kb.add(
    KeyboardButton("➕ Добавить анкету"),
    KeyboardButton("📋 Просмотр анкет"),
    KeyboardButton("🗑 Удалить анкету"),
    KeyboardButton("📋 Список анкет")
)

# ==== КОМАНДЫ ====
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("✅ Админ-панель", reply_markup=admin_kb)
    else:
        await message.answer("Бот работает")

@dp.message_handler(lambda m: m.text == "➕ Добавить анкету")
async def start_add_profile(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Введите имя:")
    await AddProfile.name.set()

@dp.message_handler(state=AddProfile.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите возраст:")
    await AddProfile.age.set()

@dp.message_handler(state=AddProfile.age)
async def get_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Введите город:")
    await AddProfile.city.set()

@dp.message_handler(state=AddProfile.city)
async def get_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Введите описание:")
    await AddProfile.about.set()

@dp.message_handler(state=AddProfile.about)
async def get_about(message: types.Message, state: FSMContext):
    await state.update_data(about=message.text)
    await message.answer("📸 Отправь фото:")
    await AddProfile.photo.set()

@dp.message_handler(state=AddProfile.photo, content_types=types.ContentType.PHOTO)
async def get_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id

    cursor.execute("""
        INSERT INTO profiles (name, age, city, about, photo_id)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["age"],
        data["city"],
        data["about"],
        photo_id
    ))

    db.commit()
    await message.answer("✅ Анкета сохранена в базе")
    await state.finish()

@dp.message_handler(lambda m: m.text == "📋 Список анкет")
async def list_profiles_btn(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT id, name, age, city FROM profiles")
    profiles = cursor.fetchall()

    if not profiles:
        await message.answer("Анкет нет")
        return

    text = "📋 Список анкет:\n\n"
    for p in profiles:
        pid, name, age, city = p
        text += f"{pid} — {name}, {age}, {city}\n"

    await message.answer(text)

@dp.message_handler(lambda m: m.text == "🗑 Удалить анкету")
async def delete_profile_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("Введите ID анкеты для удаления:")

@dp.message_handler(lambda m: m.text.isdigit())
async def delete_profile_confirm(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    pid = int(message.text)

    cursor.execute("DELETE FROM profiles WHERE id = ?", (pid,))
    db.commit()

    await message.answer(f"✅ Анкета #{pid} удалена")

@dp.message_handler(lambda m: m.text == "📋 Просмотр анкет")
async def show_profiles(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT id, name, age, city, about, photo_id FROM profiles")
    profiles = cursor.fetchall()

    if not profiles:
        await message.answer("Анкет нет ❌")
        return

    for p in profiles:
        pid, name, age, city, about, photo_id = p

        text = (
            f"🆔 ID: {pid}\n"
            f"👤 {name}\n"
            f"🎂 {age}\n"
            f"📍 {city}\n"
            f"📝 {about}"
        )

        if photo_id:
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=photo_id,
                caption=text
            )
        else:
            await message.answer(text)

# ==== ЗАПУСК ====
if __name__ == "__main__":
    executor.start_polling(dp)