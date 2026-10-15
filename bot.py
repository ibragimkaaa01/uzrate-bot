import logging
import requests
import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Твой токен
API_TOKEN = '8805256498:AAE2l0QdK6-P9dlTp0eSo9ku41_uk83W4aM'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Функция для официальных курсов ЦБ
def get_uz_rates():
    try:
        url = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        rates = {}
        for item in data:
            if item['Ccy'] in ['USD', 'EUR', 'RUB']:
                rates[item['Ccy']] = {
                    'Rate': item['Rate'],
                    'Diff': item['Diff'],
                    'Name': item['CcyNm_RU']
                }
        return rates
    except Exception as e:
        logging.error(f"Ошибка при получении курсов ЦБ: {e}")
        return None

# Функция для коммерческих курсов (Нацбанк NBU)
def get_nbu_rates():
    try:
        url = "https://nbu.uz/exchange-rates/json/"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        for item in data:
            if item['code'] == 'USD':
                # У NBU ключи называются nbu_buy_price и nbu_cell_price
                return {
                    'buy': item.get('nbu_buy_price', 'Н/Д'),
                    'sell': item.get('nbu_cell_price', 'Н/Д')
                }
    except Exception as e:
        logging.error(f"Ошибка при получении курсов NBU: {e}")
        return None

# Команда /start и клавиатура
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    kb = [
        [types.KeyboardButton(text="💵 Курсы валют ЦБ")],
        [types.KeyboardButton(text="🏦 Курсы в банках")] # Переименовали кнопку
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(
        "👋 Привет! Я UzRate — твой финансовый помощник.\n\n"
        "Выбери, что тебя интересует 👇",
        reply_markup=keyboard
    )

# Обработка кнопки "Курсы валют ЦБ"
@dp.message(lambda message: message.text == "💵 Курсы валют ЦБ")
async def show_cb_rates(message: types.Message):
    await message.answer("🔄 Запрашиваю свежие данные у ЦБ РУз...")
    rates = get_uz_rates()
    
    if not rates:
        await message.answer("❌ Извините, не удалось связаться с сервером ЦБ.")
        return
        
    text = "📊 **Официальный курс ЦБ РУз на сегодня:**\n\n"
    for ccy, info in rates.items():
        diff_sign = "+" if float(info['Diff']) > 0 else ""
        text += f"💱 **{info['Name']} ({ccy})**\n"
        text += f"🔹 1 {ccy} = {info['Rate']} сум\n"
        text += f"📉 Изменение: {diff_sign}{info['Diff']} сум\n\n"
        
    await message.answer(text, parse_mode="Markdown")

# Обработка кнопки "Курсы в банках"
@dp.message(lambda message: message.text == "🏦 Курсы в банках")
async def show_commercial_rates(message: types.Message):
    await message.answer("🔄 Собираю актуальные курсы обмена...")
    
    nbu_rates = get_nbu_rates()
    cb_rates = get_uz_rates()
    
    if not nbu_rates or not cb_rates:
        await message.answer("❌ Не удалось получить данные от банков. Попробуйте позже.")
        return
        
    cb_usd = cb_rates.get('USD', {}).get('Rate', 'Н/Д')
    
    text = (
        "🏦 **Коммерческие курсы (Доллар США - USD):**\n\n"
        "🏛 **ЦБ РУз (Для справки):**\n"
        f"Официальный: {cb_usd} сум\n\n"
        "🏦 **NBU (Нацбанк):**\n"
        f"💵 Банк покупает у вас: **{nbu_rates['buy']} сум**\n"
        f"💸 Банк продает вам: **{nbu_rates['sell']} сум**\n\n"
        "*(Скоро здесь появятся Капиталбанк, TBC и другие)*"
    )
    
    await message.answer(text, parse_mode="Markdown")

# --- ФЕЙКОВЫЙ СЕРВЕР ДЛЯ RENDER ---
async def ping(request):
    return web.Response(text="Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get('/', ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    await bot.delete_webhook(drop_pending_updates=True) 
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
