import base64
import json
import os
import aiohttp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_URL = os.getenv('DJANGO_API_URL', 'http://localhost:8080/report-api/')
AUTH_FILE = os.getenv('AUTH_FILE', 'manager_auth.json')
MONTHS_RU = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]

def get_auth_header():
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, 'r') as f:
            creds = json.load(f)
            auth_str = f"{creds['username']}:{creds['password']}"
            return {"Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}"}
    return {}

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /login <логин> <пароль>")
        return

    username, password = context.args[0], ' '.join(context.args[1:])
    with open(AUTH_FILE, 'w') as f:
        json.dump({'username': username, 'password': password}, f)
    await update.message.reply_text("✅ Учетные данные сохранены")

async def start(update: Update, _) -> None:
    commands = [
        "/login <логин> <пароль> - Авторизация",
        "/car_mileage <id> <начало> <конец> [период] [минимальный пробег] - Пробег авто",
        "/driver_time <id> <начало> <конец> [период] [минимальный пробег] - Время водителя",
        "/enterprise_active <id> <начало> <конец> [период] [минимальный пробег] - Активные авто предприятия"
    ]
    await update.message.reply_text("\n".join(commands))

def format_date(date_str: str) -> str:
    try:
        if len(date_str) == 10:  # ГГГГ-ММ-ДД
            y, m, d = map(int, date_str.split('-'))
            return f"{d} {MONTHS_RU[m-1]}"
        elif len(date_str) == 7:  # ГГГГ-ММ
            y, m = map(int, date_str.split('-'))
            return f"{MONTHS_RU[m-1]} {y}"
    except (ValueError, IndexError):
        return date_str

async def fetch_report(params: dict) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL, params=params, headers=get_auth_header()) as resp:
            if resp.status == 401:
                return {"error": "Ошибка авторизации. Используйте /login"}
            return await resp.json() if resp.status == 200 else {"error": f"Ошибка API: {resp.status}"}

async def send_report(update: Update, params: dict):
    report = await fetch_report(params)
    if 'error' in report:
        await update.message.reply_text(report['error'])
        return

    # Отчет по автомобилю/водителю
    if 'data' in report:
        lines = []
        unit = report.get("unit", "")
        for entry in report['data']:
            date = format_date(entry.get("time", ""))
            
            if "value" in entry:
                value = round(float(entry['value']))
                lines.append(f"{date}: {value} {unit}")
            elif "hours" in entry:
                lines.append(f"{date}: {entry['hours']:.1f} ч")
        
        await send_paginated(update, lines, "Отчет")

    # Отчет по предприятию - новый компактный формат
    elif isinstance(report, dict) and 'cars' in report:
        await send_enterprise_report_compact(update, report, params['min_km'])

async def send_paginated(update: Update, lines: list, title: str, chunk_size: int = 40):
    """Отправка данных с пагинацией"""
    response = []
    
    for line in lines:
        if len("\n".join(response)) + len(line) > 4000:
            await update.message.reply_text("\n".join(response))
            response = []
        response.append(line)
    
    if response:
        await update.message.reply_text("\n".join(response))

async def send_enterprise_report_compact(update: Update, report: dict, min_km: int):
    """Компактный формат отчета по предприятию с фильтрацией по пробегу"""
    cars = report.get('cars', [])
    
    # Применяем фильтр минимального пробега
    filtered_cars = [
        car for car in cars
        if any(entry.get("value", 0) >= min_km for entry in car.get("mileage_data", []))
    ]
    
    if not filtered_cars:
        await update.message.reply_text(f"Нет данных с пробегом ≥ {min_km} км")
        return

    total_pages = (len(filtered_cars) + 9) // 10
    
    for page in range(total_pages):
        start_idx = page * 10
        page_cars = filtered_cars[start_idx:start_idx + 10]
        
        response = []
        if total_pages > 1:
            response.append(f"Страница {page+1}/{total_pages}")
        elif min_km > 0:
            response.append(f"Порог пробега: ≥ {min_km} км")
        
        for car in page_cars:
            car_id = car.get('car_id', 'N/A')
            driver_name = car.get('driver_name', 'Без водителя')
            
            response.append(f"-\nАвто {car_id}, Водитель {driver_name}")
            
            for entry in car.get("mileage_data", []):
                value = round(entry.get("value", 0))
                if value < min_km:
                    continue
                date = format_date(entry.get("time", ""))
                response.append(f"  {date}: {value} км")
        
        await update.message.reply_text("\n".join(response))

async def handle_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE, report_type: str, id_name: str, default_period: str = 'day', min_km: int = 0):
    """Обработчик команд отчетов"""
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(f"Формат: /{report_type} <{id_name}> <начало> <конец> [период] [минимальный_пробег]")
        return

    # Парсинг аргументов
    params = {
        'report_type': report_type,
        id_name: args[0],
        'start_date': args[1],
        'end_date': args[2],
        'period': default_period,
        'min_km': min_km
    }

    # Обработка опциональных параметров
    if len(args) > 3:
        # Проверяем, является ли 4-й аргумент периодом или числом (min_km)
        if args[3] in ['day', 'week', 'month']:
            params['period'] = args[3]
            if len(args) > 4:
                try:
                    params['min_km'] = int(args[4])
                except ValueError:
                    await update.message.reply_text("Ошибка: минимальный пробег должен быть целым числом")
                    return
        else:
            try:
                # Если 4-й аргумент не период, пробуем интерпретировать как min_km
                params['min_km'] = int(args[3])
            except ValueError:
                await update.message.reply_text("Ошибка: неверный формат параметров. Используйте: [период] [min_km]")
                return

    await send_report(update, params)

async def car_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_report_command(update, context, 'car_mileage', 'vehicle_id', 'min_km')

async def driver_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_report_command(update, context, 'driver_time', 'driver_id', 'min_km')

async def enterprise_active(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Для предприятий используем период month по умолчанию
    await handle_report_command(update, context, 'enterprise_active_cars', 'enterprise_id', 'month', 'min_km')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error_msg = str(context.error)[:500]
    await update.message.reply_text(f"⚠️ Ошибка: {error_msg}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    handlers = [
        CommandHandler("start", start),
        CommandHandler("login", login),
        CommandHandler("car_mileage", car_mileage),
        CommandHandler("driver_time", driver_time),
        CommandHandler("enterprise_active", enterprise_active)
    ]
    
    for handler in handlers:
        app.add_handler(handler)
    
    app.add_error_handler(error_handler)
    print("Бот запущен...")
    app.run_polling()
