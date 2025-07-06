import base64
import json
import os
import aiohttp
import asyncio
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# Загрузка переменных окружения
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_URL = os.getenv('DJANGO_API_URL', 'http://localhost:8080/report-api/')
AUTH_FILE = os.getenv('manager_auth.json')

def get_auth_header():
    """Возвращает заголовок авторизации из сохраненных учетных данных"""
    try:
        if os.path.exists(AUTH_FILE):
            with open(AUTH_FILE, 'r') as f:
                credentials = json.load(f)
                auth_str = f"{credentials['username']}:{credentials['password']}"
                return {"Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}"}
        return {}
    except Exception as e:
        print(f"Ошибка получения учетных данных: {e}")
        return {}

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Разделяем сообщение на части: /set_credentials логин пароль
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Использование: /set_credentials <логин> <пароль>")
        return

    username = args[0]
    password = ' '.join(args[1:])  # Пароль может содержать пробелы

    # Сохраняем учетные данные
    credentials = {
        'username': username,
        'password': password
    }

    with open(AUTH_FILE, 'w') as f:
        json.dump(credentials, f)

    await update.message.reply_text("✅ Учетные данные успешно сохранены!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
Бот для генерации отчетов по автомобилям и предприятиям

Команды:
/login <логин> <пароль> - Авторизация менеджера
/car_mileage <vehicle_id> <start_date> <end_date> [period] - Пробег автомобиля
/driver_time <driver_id> <start_date> <end_date> [period] - Время езды водителя 
/enterprise_active <enterprise_id> <start_date> <end_date> [period] - Пробег активных автомобилей предприятия

Параметры:
- vehicle_id/driver_id/enterprise_id: ID объекта
- start_date/end_date: Даты отчета в формате ГГГГ-ММ-ДД
- period: Период вывода данных (day, week, month). По умолчанию: day
"""
    await update.message.reply_text(help_text)

async def fetch_report(params: dict) -> dict:
    """Выполняет GET-запрос к API с Basic Auth."""
    headers = get_auth_header()
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL, params=params, headers=headers) as resp:
            if resp.status == 401:
                return {"error": "Неавторизован: проверьте учётные данные (/login)"}
            if resp.status != 200:
                return {"error": f"API error: {resp.status}"}
            return await resp.json()

async def send_report(update: Update, params: dict):
    report = await fetch_report(params)
    if 'error' in report:
        await update.message.reply_text(f"Ошибка: {report['error']}")
    else:
        # Форматирование ответа для читаемости
        response_text = "\n".join([f"{key}: {value}" for key, value in report.items()])
        await update.message.reply_text(f"📈 Отчет:\n{response_text}")

async def car_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Недостаточно аргументов. Формат: /car_mileage <vehicle_id> <start_date> <end_date> [period]")
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
        await update.message.reply_text("Недостаточно аргументов. Формат: /driver_time <driver_id> <start_date> <end_date> [period]")
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
        await update.message.reply_text("Недостаточно аргументов. Формат: /enterprise_active <enterprise_id> <start_date> <end_date> [period]")
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
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("car_mileage", car_mileage))
    app.add_handler(CommandHandler("driver_time", driver_time))
    app.add_handler(CommandHandler("enterprise_active", enterprise_active))

    print("Бот запущен...")
    app.run_polling()
