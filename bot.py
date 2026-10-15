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

# Функция для курсов
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
        logging.error(f"Ошибка при получении курсов: {e}")
        return None

# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    kb = [
        [types.KeyboardButton(text="💵 Курсы валют ЦБ")],
        [types.KeyboardButton(text="🏦 Самый выгодный банк (Скоро)")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(
        "👋 Привет! Я UzRate — твой финансовый помощник.\n\n"
        "Я помогу тебе находить лучшие курсы валют в Узбекистане. Нажми на кнопку ниже 👇",
        reply_markup=keyboard
    )

# Кнопка курсов
@dp.message(lambda message: message.text == "💵 Курсы валют ЦБ")
async def show_rates(message: types.Message):
    await message.answer("🔄 Запрашиваю свежие данные у ЦБ РУз...")
    rates = get_uz_rates()
    
    if not rates:
        await message.answer("❌ Извините, не удалось связаться с сервером. Попробуйте позже.")
        return
        
    text = "📊 **Официальный курс ЦБ РУз на сегодня:**\n\n"
    for ccy, info in rates.items():
        diff_sign = "+" if float(info['Diff']) > 0 else ""
        text += f"💱 **{info['Name']} ({ccy})**\n"
        text += f"🔹 1 {ccy} = {info['Rate']} сум\n"
        text += f"📉 Изменение: {diff_sign}{info['Diff']} сум\n\n"
        
    await message.answer(text, parse_mode="Markdown")

# --- ДОБАВЛЕННЫЙ БЛОК: ФЕЙКОВЫЙ СЕРВЕР ДЛЯ RENDER ---
async def ping(request):
    return web.Response(text="Bot is running!")

async def main():
    # Запускаем "заглушку" для Render
    app = web.Application()
    app.router.add_get('/', ping)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render передает свой порт, мы его ловим
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    # Запускаем самого бота
    await bot.delete_webhook(drop_pending_updates=True) 
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
