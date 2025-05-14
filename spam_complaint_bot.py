"""spam_complaint_bot.py
Минимально‑рабочий Telegram‑бот (aiogram v3) для генерации жалоб в УФАС на спам‑звонки и СМС.
Перед запуском:
  export BOT_TOKEN=YOUR_TOKEN_HERE
  pip install -r requirements.txt
  python spam_complaint_bot.py
"""
import asyncio, os, sqlite3
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

DB = "complaints.db"

def init_db():
    conn = sqlite3.connect(DB)
    with conn:
        conn.executescript("""CREATE TABLE IF NOT EXISTS users(
    telegram_id INTEGER PRIMARY KEY,
    fio TEXT, address TEXT, email TEXT, phone TEXT,
    region TEXT, consent INTEGER
);
CREATE TABLE IF NOT EXISTS complaints(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT, offender TEXT, stamp TEXT,
    robot INTEGER, content TEXT, region TEXT,
    attachment TEXT
);""")
    conn.close()

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

class Data(StatesGroup):
    fio = State()
    address = State()
    email = State()
    phone = State()

class Ticket(StatesGroup):
    type = State()
    offender = State()
    stamp = State()
    robot = State()
    content = State()
    attachment = State()
    confirm = State()

def complaint_text(user, data):
    txt = f"""Жалоба на нарушение законодательства о рекламе

Информация о нарушении:
- Номер: {data['offender']}
- Дата/время: {data['stamp']}
- Форма: {data['type']}
- Робот: {'Да' if data['robot'] else 'Нет'}
- Согласие не давалось
- Содержание: {data['content']}

Заявитель:
{user['fio']}
{user['address']}
{user['email']}
{user['phone']}

Региональное УФАС: {user['region']}

Дата: {datetime.now().strftime('%d.%m.%Y')}
Подпись: __________
"""
    return txt

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN env var")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()
dp.include_router(router)

@router.message(Command("start"))
async def start(m: types.Message):
    conn = db()
    u = conn.execute("SELECT consent FROM users WHERE telegram_id=?", (m.from_user.id,)).fetchone()
    if not u or not u['consent']:
        kb = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Согласен")]],
            resize_keyboard=True, one_time_keyboard=True)
        await m.answer("Для работы бота требуется согласие на обработку персональных данных (ФЗ‑152). Нажмите Согласен.", reply_markup=kb)
    else:
        await m.answer("Добро пожаловать! /данные — персональные данные, /жалоба — новая жалоба.")

@router.message(lambda msg: msg.text and msg.text.lower() == "согласен")
async def consent(m: types.Message):
    conn = db()
    with conn:
        conn.execute("INSERT OR REPLACE INTO users(telegram_id, consent) VALUES(?,1)", (m.from_user.id,))
    await m.answer("Спасибо! Введите /данные для заполнения анкеты.", reply_markup=types.ReplyKeyboardRemove())

@router.message(Command("данные"))
async def data_start(m: types.Message, state: FSMContext):
    await m.answer("Введите ФИО:")
    await state.set_state(Data.fio)

@router.message(Data.fio)
async def data_fio(m: types.Message, state: FSMContext):
    await state.update_data(fio=m.text.strip())
    await m.answer("Адрес:")
    await state.set_state(Data.address)

@router.message(Data.address)
async def data_addr(m: types.Message, state: FSMContext):
    await state.update_data(address=m.text.strip())
    await m.answer("E‑mail:")
    await state.set_state(Data.email)

@router.message(Data.email)
async def data_email(m: types.Message, state: FSMContext):
    await state.update_data(email=m.text.strip())
    await m.answer("Телефон (ваш номер):")
    await state.set_state(Data.phone)

@router.message(Data.phone)
async def data_phone(m: types.Message, state: FSMContext):
    data = await state.update_data(phone=m.text.strip())
    conn = db()
    with conn:
        conn.execute("""INSERT OR REPLACE INTO users
            (telegram_id,fio,address,email,phone,consent) VALUES (?,?,?,?,?,1)
        """, (m.from_user.id, data['fio'], data['address'], data['email'], data['phone']))
    await m.answer("Данные сохранены! /регион — выбрать УФАС, /жалоба — создать жалобу.")
    await state.clear()

@router.message(Command("регион"))
async def set_region_prompt(m: types.Message):
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=r)] for r in ["Москва","Московская область","Санкт-Петербург"]],
        resize_keyboard=True, one_time_keyboard=True)
    await m.answer("Выберите ваш регион:", reply_markup=kb)

@router.message(lambda msg: msg.text in ["Москва","Московская область","Санкт-Петербург"])
async def set_region(m: types.Message):
    conn = db()
    with conn:
        conn.execute("UPDATE users SET region=? WHERE telegram_id=?", (m.text, m.from_user.id))
    await m.answer(f"Регион сохранён: {m.text}", reply_markup=types.ReplyKeyboardRemove())

@router.message(Command("жалоба"))
async def ticket_start(m: types.Message, state: FSMContext):
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Звонок"), types.KeyboardButton(text="СМС")]],
        resize_keyboard=True, one_time_keyboard=True)
    await m.answer("Звонок или СМС?", reply_markup=kb)
    await state.set_state(Ticket.type)

@router.message(Ticket.type)
async def t_type(m: types.Message, state: FSMContext):
    await state.update_data(type=m.text)
    await m.answer("Номер нарушителя:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Ticket.offender)

@router.message(Ticket.offender)
async def t_offender(m: types.Message, state: FSMContext):
    await state.update_data(offender=m.text.strip())
    await m.answer("Дата/время (15.05.2025 14:20):")
    await state.set_state(Ticket.stamp)

@router.message(Ticket.stamp)
async def t_stamp(m: types.Message, state: FSMContext):
    await state.update_data(stamp=m.text.strip())
    await m.answer("Использовался робот? (Да/Нет)")
    await state.set_state(Ticket.robot)

@router.message(Ticket.robot)
async def t_robot(m: types.Message, state: FSMContext):
    await state.update_data(robot=m.text.lower().startswith("д"))
    await m.answer("Краткое содержание рекламы:")
    await state.set_state(Ticket.content)

@router.message(Ticket.content)
async def t_content(m: types.Message, state: FSMContext):
    await state.update_data(content=m.text.strip())
    await m.answer("Пришлите скрин или аудио (не обязательно) или напишите Нет:")
    await state.set_state(Ticket.attachment)

@router.message(Ticket.attachment, F.photo | F.document | F.text)
async def t_attach(m: types.Message, state: FSMContext):
    path = None
    if m.photo:
        f = await bot.get_file(m.photo[-1].file_id)
        path = f"attach_{f.file_id}.jpg"
        await bot.download_file(f.file_path, path)
    elif m.document:
        f = await bot.get_file(m.document.file_id)
        path = m.document.file_name
        await bot.download_file(f.file_path, path)
    await state.update_data(attachment=path)
    await m.answer("Подтвердить? (Да/Нет)")
    await state.set_state(Ticket.confirm)

@router.message(Ticket.confirm)
async def t_confirm(m: types.Message, state: FSMContext):
    if not m.text.lower().startswith("д"):
        await m.answer("Отменено.")
        await state.clear()
        return
    data = await state.get_data()
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE telegram_id=?", (m.from_user.id,)).fetchone()
    text = complaint_text(user, data)
    with conn:
        conn.execute("""INSERT INTO complaints(user_id,type,offender,stamp,robot,content,region,attachment)
                        VALUES(?,?,?,?,?,?,?,?)""",
                     (user['telegram_id'], data['type'], data['offender'], data['stamp'],
                      int(data['robot']), data['content'], user['region'], data['attachment']))
    await m.answer("<b>Текст вашей жалобы:</b>\n\n" + text)
    await m.answer("Скопируйте текст и отправьте в УФАС. Спасибо!")
    await state.clear()

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


# ---------- mailto integration ----------
from mailto_link import generate_mailto

@router.message(Command("ссылка"))
async def mailto_link_test(message: types.Message):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE telegram_id=?", (message.from_user.id,)).fetchone()
    if not user:
        await message.answer("Сначала введите персональные данные командой /данные")
        return
    last = conn.execute("SELECT * FROM complaints WHERE user_id=? ORDER BY id DESC LIMIT 1", (user["telegram_id"],)).fetchone()
    if not last:
        await message.answer("Жалобы не найдены. Сначала подайте жалобу через /жалоба")
        return
    data = {
        "type": last["complaint_type"],
        "offender": last["offender_number"],
        "dt": last["datetime"],
        "robot": bool(last["robot_used"]),
        "content": last["content"],
        "region": last["region"]
    }
    text = build_complaint_text(user, data)
    region_email = {
        "Москва": "to@fas.gov.ru",
        "Московская область": "mo@fas.gov.ru",
        "Санкт-Петербург": "spb@fas.gov.ru",
        "Краснодарский край": "krasnodar@fas.gov.ru",
        "Республика Татарстан": "tatarstan@fas.gov.ru"
    }.get(data["region"], "to@fas.gov.ru")

    mailto = generate_mailto(region_email, "Жалоба на рекламу без согласия", text)
    await message.answer(f"Ссылка для отправки жалобы в УФАС:\n<a href='{mailto}'>Отправить e-mail</a>", parse_mode="HTML")
