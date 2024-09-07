import asyncio
import aiosqlite
import whois
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import API_TOKEN, WELCOME_IMAGE_URL

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

waiting_for_domain = False

async def db_setup():
    async with aiosqlite.connect('users.db') as db:
        await db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, user_id INTEGER UNIQUE, join_date TEXT)')
        await db.commit()

async def add_user(user_id, join_date):
    async with aiosqlite.connect('users.db') as db:
        await db.execute('INSERT OR IGNORE INTO users (user_id, join_date) VALUES (?, ?)', (user_id, join_date))
        await db.commit()

async def on_startup(dp):
    await db_setup()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    join_date = message.date.isoformat()
    await add_user(user_id, join_date)

    await message.answer_photo(WELCOME_IMAGE_URL, caption="Добро пожаловать! Выберите действие:", reply_markup=main_menu())

def main_menu():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Проверить домен", callback_data="check_domain"))
    keyboard.add(types.InlineKeyboardButton("Автор бота", url="https://lolz.live/ubel/"))
    return keyboard

@dp.callback_query_handler(lambda c: c.data == 'check_domain')
async def cb_check_domain(callback_query: types.CallbackQuery):
    global waiting_for_domain
    waiting_for_domain = True
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Введите домен для проверки:")

@dp.message_handler(lambda message: waiting_for_domain)
async def handle_domain_check(message: types.Message):
    global waiting_for_domain
    domain = message.text
    await check_domain(domain, message.from_user.id)
    waiting_for_domain = False
    await bot.send_photo(message.from_user.id, WELCOME_IMAGE_URL, caption="Выберите действие:", reply_markup=main_menu())

async def check_domain(domain, user_id):
    try:
        w = whois.whois(domain)
        creation_date = w.creation_date.strftime('%Y-%m-%d') if w.creation_date else "Неизвестно"
        expiration_date = w.expiration_date.strftime('%Y-%m-%d') if w.expiration_date else "Неизвестно"
        name_servers = ", ".join(w.name_servers) if w.name_servers else "Неизвестно"

        response = (
            f"Домен: {domain}\n"
            f"Дата создания: {creation_date}\n"
            f"Дата истечения: {expiration_date}\n"
            f"Серверы имен: {name_servers}"
        )

        await bot.send_message(user_id, response)
    except Exception as e:
        await bot.send_message(user_id, f"Ошибка: {e}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
