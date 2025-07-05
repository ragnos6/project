import os
import aiohttp
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Загрузка переменных окружения
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_URL = os.getenv('DJANGO_API_URL', 'http://localhost:8080/report-api/')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
📊 Бот для генерации отчетов по автомобилям и предприятиям

Доступные команды:
/car_mileage <vehicle_id> <start_date> <end_date> [period]
/driver_time <driver_id> <start_date> <end_date> [period]
/enterprise_active <enterprise_id> <start_date> <end_date> [period]

📝 Параметры:
- vehicle_id/driver_id/enterprise_id: ID объекта
- start_date/end_date: Дата в формате ГГГГ-ММ-ДД
- period (опционально): Детализация (day, week, month). По умолчанию: day
"""
    await update.message.reply_text(help_text)

async def fetch_report(params: dict) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL, params=params) as response:
            if response.status == 200:
                return await response.json()
            return {"error": f"API error: {response.status}"}

async def send_report(update: Update, params: dict):
    report = await fetch_report(params)
    if 'error' in report:
        await update.message.reply_text(f"❌ Ошибка: {report['error']}")
    else:
        # Форматирование ответа для читаемости
        response_text = "\n".join([f"{key}: {value}" for key, value in report.items()])
        await update.message.reply_text(f"📈 Отчет:\n{response_text}")

async def car_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("⚠️ Недостаточно аргументов. Формат: /car_mileage <vehicle_id> <start_date> <end_date> [period]")
        return

    params = {
        'report_type': 'car_mileage',
        'vehicle_id': args[0],
        'start_date': args[1],
        'end_date': args[2],
        'period': args[3] if len(args) > 3 else 'day'
    }
    await send_report(update, params)

async def driver_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("⚠️ Недостаточно аргументов. Формат: /driver_time <driver_id> <start_date> <end_date> [period]")
        return

    params = {
        'report_type': 'driver_time',
        'driver_id': args[0],
        'start_date': args[1],
        'end_date': args[2],
        'period': args[3] if len(args) > 3 else 'day'
    }
    await send_report(update, params)

async def enterprise_active(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("⚠️ Недостаточно аргументов. Формат: /enterprise_active <enterprise_id> <start_date> <end_date> [period]")
        return

    params = {
        'report_type': 'enterprise_active_cars',
        'enterprise_id': args[0],
        'start_date': args[1],
        'end_date': args[2],
        'period': args[3] if len(args) > 3 else 'day'
    }
    await send_report(update, params)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("car_mileage", car_mileage))
    app.add_handler(CommandHandler("driver_time", driver_time))
    app.add_handler(CommandHandler("enterprise_active", enterprise_active))
    
    print("Бот запущен...")
    app.run_polling()
