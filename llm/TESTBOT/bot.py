import os
import json
import requests
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import asyncio
import logging
from message_handler import send_gradual_message

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('medical_assistant_bot')

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Путь к файлу с данными
DATA_FILE = '../data.json'

def load_conversation_history():
    """Загружает историю диалогов из файла"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_conversation_history(history):
    """Сохраняет историю диалогов в файл"""
    with open(DATA_FILE, 'w', encoding='utf-8') as file:
        json.dump(history, file, ensure_ascii=False, indent=2)

@dp.message(Command("start"))
async def start_command(message: Message):
    user_id = str(message.from_user.id)
    logger.info(f"Новый пользователь начал диалог: {user_id}")
    
    conversation_history = load_conversation_history()
    if user_id not in conversation_history:
        conversation_history[user_id] = []
        save_conversation_history(conversation_history)
        logger.info(f"Создана новая история диалога для пользователя {user_id}")
    
    await message.answer(
        "Здравствуйте! Я медицинский ассистент. Опишите, пожалуйста, что вас беспокоит, "
        "и я постараюсь помочь определить возможный диагноз и порекомендовать специалиста."
    )

@dp.message(Command("clear"))
async def clear_command(message: Message):
    user_id = str(message.from_user.id)
    logger.info(f"Очистка истории диалога для пользователя {user_id}")
    
    conversation_history = load_conversation_history()
    if user_id in conversation_history:
        conversation_history[user_id] = []
        save_conversation_history(conversation_history)
    
    await message.answer("История диалога очищена. Можете начать новую консультацию.")

@dp.message()
async def handle_message(message: Message):
    """Обработчик текстовых сообщений"""
    user_id = str(message.from_user.id)
    user_message = message.text
    
    logger.info(f"Получено новое сообщение от пользователя {user_id}")
    
    conversation_history = load_conversation_history()
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })
    
    try:
        logger.info("Отправка запроса к серверу")
        response = requests.post(
            'http://localhost:5000/check-uc',
            json={'prompt': conversation_history[user_id]},
            stream=True
        )
        
        if response.status_code == 200:
            # Используем новую функцию для постепенной отправки сообщения
            full_response = await send_gradual_message(message, response)
            
            if full_response:
                conversation_history[user_id].append({
                    "role": "assistant",
                    "content": full_response
                })
                save_conversation_history(conversation_history)
                logger.info("История диалога обновлена")
        else:
            logger.error(f"Ошибка сервера: {response.status_code}")
            await message.answer(
                "Извините, произошла ошибка при обработке вашего запроса. "
                "Пожалуйста, попробуйте позже."
            )
    
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        await message.answer(
            "Извините, произошла ошибка при обработке вашего запроса. "
            "Пожалуйста, попробуйте позже."
        )

async def main():
    logger.info("Запуск бота медицинского ассистента")
    if not os.path.exists(DATA_FILE):
        save_conversation_history({})
        logger.info("Создан новый файл истории диалогов")
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
