"""
Телеграм-бот с интегрированным Kafka-консьюмером для уведомлений о CRUD-операциях с автомобилями.

Требования:
- python 3.9+
- pip install python-telegram-bot aiohttp aiokafka python-dotenv

Переменные окружения (обычно в .env):
- TELEGRAM_BOT_TOKEN - токен бота
- DJANGO_API_URL - базовый URL вашего Django API (по умолчанию http://localhost:8080/report-api/)
- AUTH_FILE - файл с базовой авторизацией менеджера (по умолчанию manager_auth.json)
- KAFKA_BOOTSTRAP_SERVERS - адрес Kafka bootstrap, например localhost:9092
- KAFKA_TOPIC - topic для событий (по умолчанию vehicle.events)

Файл объединяет команды бота (login, отчёты) и фоновую задачу, слушающую Kafka и рассылающую уведомления менеджерам.
"""

import os
import json
import base64
import asyncio
import logging
from datetime import datetime

import aiohttp
from dotenv import load_dotenv
from aiokafka import AIOKafkaConsumer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Загружаем .env
load_dotenv()

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_URL = os.getenv('DJANGO_API_URL', 'http://localhost:8080/report-api/')
AUTH_FILE = os.getenv('AUTH_FILE', 'manager_auth.json')
KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'vehicle.events')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'bot-notifier-group')
MANAGER_FILE = os.path.join(os.path.dirname(__file__), AUTH_FILE)

MONTHS_RU = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]

# ---------------------- Утилиты авторизации ----------------------

def get_auth_header():
    """Возвращает заголовок Authorization с basic-auth, если файл с учётными данными существует."""
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, 'r') as f:
                creds = json.load(f)
                # Если это список, берем первого менеджера (для API запросов)
                if isinstance(creds, list) and len(creds) > 0:
                    creds = creds[0]
                auth_str = f"{creds['username']}:{creds['password']}"
                return {"Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}"}
        except Exception as e:
            logger.exception('Не удалось прочитать AUTH_FILE: %s', e)
    return {}

# ---------------------- Форматирование и запросы отчётов ----------------------

def format_date(date_str: str) -> str:
    try:
        if len(date_str) == 10:  # YYYY-MM-DD
            y, m, d = map(int, date_str.split('-'))
            return f"{d} {MONTHS_RU[m-1]}"
        elif len(date_str) == 7:  # YYYY-MM
            y, m = map(int, date_str.split('-'))
            return f"{MONTHS_RU[m-1]} {y}"
    except (ValueError, IndexError):
        return date_str

async def fetch_report(params: dict) -> dict:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(API_URL, params=params, headers=get_auth_header()) as resp:
                if resp.status == 401:
                    return {"error": "Ошибка авторизации. Используйте /login"}
                return await resp.json() if resp.status == 200 else {"error": f"Ошибка API: {resp.status}"}
        except Exception as e:
            logger.exception('Ошибка при запросе отчёта: %s', e)
            return {"error": "Ошибка запроса к API"}

# ---------------------- Команды бота (login, start, отчёты) ----------------------

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Логин менеджера с привязкой к предприятию и chat_id.
    Использование:
    /login <логин> <пароль> <enterprise_id>
    """
    if len(context.args) < 3:
        await update.message.reply_text(
            "Использование: /login <логин> <пароль> <enterprise_id>"
        )
        return

    username, password = context.args[0], context.args[1]
    
    try:
        enterprise_id = int(context.args[2])
    except ValueError:
        await update.message.reply_text("Ошибка: enterprise_id должен быть числом")
        return

    manager_data = {
        "username": username,
        "password": password,
        "enterprise_id": enterprise_id,
        "telegram_chat_id": update.effective_chat.id
    }

    try:
        # Если файл уже существует с другими менеджерами, читаем их
        if os.path.exists(AUTH_FILE):
            with open(AUTH_FILE, 'r', encoding='utf-8') as f:
                try:
                    existing = json.load(f)
                    if not isinstance(existing, list):
                        existing = []
                except json.JSONDecodeError:
                    existing = []
        else:
            existing = []

        # Проверяем, есть ли уже этот менеджер и обновляем
        updated = False
        for i, m in enumerate(existing):
            if m.get("telegram_chat_id") == manager_data["telegram_chat_id"]:
                existing[i] = manager_data
                updated = True
                break
        if not updated:
            existing.append(manager_data)

        # Сохраняем обратно
        with open(AUTH_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        await update.message.reply_text("✅ Учетные данные и предприятие сохранены")
    except Exception as e:
        logger.exception("Не удалось сохранить учетные данные: %s", e)
        await update.message.reply_text("Ошибка при сохранении учетных данных")

async def start_cmd(update: Update, _) -> None:
    commands = [
        "/login <логин> <пароль> <enterprise_id> - Авторизация",
        "/car_mileage <id> <начало> <конец> [период] [минимальный пробег] - Пробег авто",
        "/driver_time <id> <начало> <конец> [период] [минимальный пробег] - Время водителя",
        "/enterprise_active <id> <начало> <конец> [период] [минимальный пробег] - Активные авто предприятия"
    ]
    await update.message.reply_text("\n".join(commands))

async def send_paginated(update: Update, lines: list, title: str, chunk_size: int = 40):
    response = []
    for line in lines:
        if len("\n".join(response)) + len(line) > 4000:
            await update.message.reply_text("\n".join(response))
            response = []
        response.append(line)
    if response:
        await update.message.reply_text("\n".join(response))

async def send_enterprise_report_compact(update: Update, report: dict, min_km: int):
    cars = report.get('cars', [])
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

async def send_report(update: Update, params: dict):
    report = await fetch_report(params)
    if 'error' in report:
        await update.message.reply_text(report['error'])
        return

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
    elif isinstance(report, dict) and 'cars' in report:
        await send_enterprise_report_compact(update, report, params.get('min_km', 0))

async def handle_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE, report_type: str, id_name: str, default_period: str = 'day', default_min_km: int = 0):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(f"Формат: /{report_type} <{id_name}> <начало> <конец> [период] [минимальный_пробег]")
        return

    params = {
        'report_type': report_type,
        id_name: args[0],
        'start_date': args[1],
        'end_date': args[2],
        'period': default_period,
        'min_km': default_min_km
    }

    if len(args) > 3:
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
                params['min_km'] = int(args[3])
            except ValueError:
                await update.message.reply_text("Ошибка: неверный формат параметров. Используйте: [период] [min_km]")
                return

    await send_report(update, params)

async def car_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_report_command(update, context, 'car_mileage', 'vehicle_id', 'day', 0)

async def driver_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_report_command(update, context, 'driver_time', 'driver_id', 'day', 0)

async def enterprise_active(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_report_command(update, context, 'enterprise_active_cars', 'enterprise_id', 'month', 0)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error_msg = str(context.error)[:500]
    try:
        await update.message.reply_text(f"⚠️ Ошибка: {error_msg}")
    except Exception:
        logger.exception('Не удалось отправить сообщение об ошибке')

# ---------------------- Kafka: получение менеджеров и обработка сообщений ----------------------

async def fetch_managers_for_enterprise(enterprise_id):
    """
    Возвращает список менеджеров для enterprise из manager_auth.json.
    """
    if not os.path.exists(MANAGER_FILE):
        logger.warning("Файл менеджеров %s не найден", MANAGER_FILE)
        return []

    try:
        with open(MANAGER_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Всегда работаем со списком
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            data = []
            
        # Фильтруем по enterprise_id
        managers = [
            m for m in data 
            if m.get('enterprise_id') == enterprise_id and m.get('telegram_chat_id')
        ]
        
        if not managers:
            logger.info("Менеджеры для enterprise %s не найдены в файле", enterprise_id)
        
        return managers
    except Exception as e:
        logger.exception("Ошибка чтения менеджеров из файла: %s", e)
        return []

async def handle_kafka_message(app, msg_value: dict):
    """Формирует текст уведомления и рассылает менеджерам предприятия."""
    try:
        # Проверка обязательных полей
        if not isinstance(msg_value, dict):
            logger.error("Некорректный формат сообщения Kafka: не словарь")
            return
            
        action = msg_value.get('action')
        payload = msg_value.get('payload', {})
        enterprise_id = payload.get('enterprise_id')
        
        if not all([action, enterprise_id]):
            logger.error("В сообщении Kafka отсутствуют обязательные поля: action=%s, enterprise_id=%s", 
                        action, enterprise_id)
            return

        vid = payload.get('id', 'N/A')

        lines = [f"Автомобиль #{vid} — действие: {action.upper()}"]
        if payload.get('model_id'):
            lines.append(f"Модель (id): {payload.get('model_id')}")
        if payload.get('mileage') is not None:
            lines.append(f"Пробег: {payload.get('mileage')} км")
        if payload.get('purchase_date'):
            lines.append(f"Дата покупки: {payload.get('purchase_date')}")

        changed = payload.get('changed_fields', {})
        if changed:
            lines.append('\nИзменённые поля:')
            for k, v in changed.items():
                old = v.get('old')
                new = v.get('new')
                lines.append(f" - {k}: {old} -> {new}")

        text = '\n'.join(lines)

        managers = await fetch_managers_for_enterprise(enterprise_id)
        if not managers:
            logger.info('Менеджеры для enterprise %s не найдены, уведомление не отправлено', enterprise_id)
            return

        for m in managers:
            chat_id = m.get('telegram_chat_id')
            if not chat_id:
                continue
            try:
                await app.bot.send_message(chat_id=chat_id, text=text)
                logger.info('Уведомление отправлено менеджеру %s', chat_id)
            except Exception as e:
                logger.exception('Не удалось отправить уведомление %s менеджеру %s: %s', vid, chat_id, e)
                
    except Exception as e:
        logger.exception('Критическая ошибка в handle_kafka_message: %s', e)

async def kafka_consumer_task(app):
    """Фоновая задача — слушает Kafka topic и обрабатывает сообщения."""
    consumer = None
    retry_count = 0
    max_retries = 5
    
    while retry_count < max_retries:
        try:
            consumer = AIOKafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                group_id=KAFKA_GROUP_ID,
                enable_auto_commit=True,
                auto_offset_reset='earliest'
            )

            await consumer.start()
            logger.info('Kafka consumer started, topic=%s, bootstrap=%s', KAFKA_TOPIC, KAFKA_BOOTSTRAP)
            retry_count = 0  # Сброс счетчика при успешном подключении
            
            async for msg in consumer:
                try:
                    raw = msg.value
                    if isinstance(raw, (bytes, bytearray)):
                        raw = raw.decode('utf-8')
                    payload = json.loads(raw)
                    await handle_kafka_message(app, payload)
                except json.JSONDecodeError as e:
                    logger.error('Не удалось распарсить JSON сообщение Kafka: %s', e)
                except Exception as e:
                    logger.exception('Ошибка обработки сообщения Kafka: %s', e)
                    
        except asyncio.CancelledError:
            logger.info('Kafka consumer task cancelled')
            break
        except Exception as e:
            retry_count += 1
            logger.error('Ошибка в Kafka consumer task (попытка %d/%d): %s', 
                        retry_count, max_retries, e)
            
            if retry_count < max_retries:
                wait_time = 2 ** retry_count  # Экспоненциальная задержка
                logger.info('Повторная попытка подключения через %d секунд...', wait_time)
                await asyncio.sleep(wait_time)
            else:
                logger.error('Превышено максимальное количество попыток подключения к Kafka')
                break
        finally:
            if consumer:
                try:
                    await consumer.stop()
                except Exception:
                    logger.exception('Ошибка при остановке Kafka consumer')

# ---------------------- Main: регистрация команд и запуск ----------------------

def build_app():
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен!")
        
    app = ApplicationBuilder().token(TOKEN).build()

    handlers = [
        CommandHandler("start", start_cmd),
        CommandHandler("login", login),
        CommandHandler("car_mileage", car_mileage),
        CommandHandler("driver_time", driver_time),
        CommandHandler("enterprise_active", enterprise_active),
    ]
    for h in handlers:
        app.add_handler(h)

    app.add_error_handler(error_handler)

    return app

def main():
    """Основная функция запуска бота."""
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        return

    app = build_app()
    
    # Создаем и запускаем Kafka consumer в фоне
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Запускаем Kafka consumer в отдельной задаче
    kafka_task = loop.create_task(kafka_consumer_task(app))
    
    try:
        # Запускаем бота в основном потоке
        logger.info("Запуск бота...")
        app.run_polling()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.exception("Критическая ошибка: %s", e)
    finally:
        # Отменяем Kafka task при завершении
        if not kafka_task.done():
            kafka_task.cancel()
        loop.run_until_complete(asyncio.sleep(1))  # Даем время на завершение
        loop.close()

if __name__ == "__main__":
    main()
