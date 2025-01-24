import os
import json
import requests
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import asyncio
from message_handler import send_gradual_message
from logging_config import setup_logger
from typing import Tuple, Optional

# Инициализация логгеров
bot_logger = setup_logger('bot', 'API_LOGGING')
file_logger = setup_logger('bot_file', 'FILE_OPERATIONS_LOGGING')

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
        file_logger.info("Загрузка истории диалогов из файла")
        with open(DATA_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Проверяем структуру данных
            if not isinstance(data, dict):
                file_logger.warning("Некорректная структура данных в файле истории. Создаем новый.")
                return {}
        file_logger.info(f"Загружена история для {len(data)} пользователей")
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        file_logger.warning(f"Ошибка при загрузке истории: {e}. Создаем новый файл.")
        return {}

def save_conversation_history(history):
    """Сохраняет историю диалогов в файл"""
    try:
        file_logger.info("Сохранение истории диалогов")
        with open(DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(history, file, ensure_ascii=False, indent=2)
        file_logger.info(f"Сохранена история для {len(history)} пользователей")
    except Exception as e:
        file_logger.error(f"Ошибка при сохранении истории: {e}")

def create_user_session(user_id: str):
    """Создает новую сессию для пользователя"""
    bot_logger.info(f"Создание новой сессии для пользователя {user_id}")
    return {
        "messages": [],
        "current_stage": "SYMPTOMS",
        "symptoms": [],
        "patient_info": {
            "age": None,
            "has_chronic_diseases": False,
            "chronic_diseases": [],
            "has_allergies": False,
            "allergies": []
        }
    }

@dp.message(Command("start"))
async def start_command(message: Message):
    user_id = str(message.from_user.id)
    bot_logger.info(f"Новый пользователь начал диалог: {user_id}")
    
    conversation_history = load_conversation_history()
    if user_id not in conversation_history:
        conversation_history[user_id] = create_user_session(user_id)
    
    # Отправляем запрос к серверу для получения приветственных сообщений
    try:
        response = requests.post(
            'http://localhost:5000/get-welcome-messages',
            json={
                'user_id': user_id,
                'is_clear_command': False
            }
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if 'error' in response_data:
                bot_logger.error(f"Ошибка сервера: {response_data['error']}")
                await message.answer("Извините, произошла ошибка. Попробуйте позже.")
                return

            conversation_state = response_data.get('conversation_state', {})
            # Сохраняем состояние диалога
            conversation_history[user_id].update({
                "current_stage": conversation_state.get("current_stage", "SYMPTOMS"),
                "symptoms": conversation_state.get("symptoms", []),
                "patient_info": conversation_state.get("patient_info", {})
            })
            
            # Отправляем приветственные сообщения
            for message_text in response_data.get('messages', []):
                conversation_history[user_id]["messages"].append({
                    "role": "assistant",
                    "content": message_text
                })
                await message.answer(message_text)
        else:
            # Если произошла ошибка, отправляем стандартное приветствие
            greeting_message = (
                "Здравствуйте! Я медицинский ассистент, созданный для помощи в предварительной диагностике. "
                "Пожалуйста, опишите, что вас беспокоит."
            )
            conversation_history[user_id]["messages"].append({
                "role": "assistant",
                "content": greeting_message
            })
            await message.answer(greeting_message)
    except Exception as e:
        bot_logger.error(f"Ошибка при обработке запроса: {str(e)}")
        greeting_message = (
            "Здравствуйте! Я медицинский ассистент, созданный для помощи в предварительной диагностике. "
            "Пожалуйста, опишите, что вас беспокоит."
        )
        conversation_history[user_id]["messages"].append({
            "role": "assistant",
            "content": greeting_message
        })
        await message.answer(greeting_message)
    
    save_conversation_history(conversation_history)
    bot_logger.info(f"Создана новая сессия для пользователя {user_id}")

@dp.message(Command("clear"))
async def clear_command(message: Message):
    user_id = str(message.from_user.id)
    bot_logger.info(f"Очистка сессии для пользователя {user_id}")
    
    conversation_history = load_conversation_history()
    conversation_history[user_id] = create_user_session(user_id)
    
    # Отправляем запрос к серверу для получения приветственных сообщений
    try:
        response = requests.post(
            'http://localhost:5000/get-welcome-messages',
            json={
                'user_id': user_id,
                'is_clear_command': True
            }
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if 'error' in response_data:
                bot_logger.error(f"Ошибка сервера: {response_data['error']}")
                await message.answer("Извините, произошла ошибка. Попробуйте позже.")
                return

            conversation_state = response_data.get('conversation_state', {})
            # Сохраняем состояние диалога
            conversation_history[user_id].update({
                "current_stage": conversation_state.get("current_stage", "SYMPTOMS"),
                "symptoms": conversation_state.get("symptoms", []),
                "patient_info": conversation_state.get("patient_info", {})
            })
            
            # Отправляем сообщения
            for message_text in response_data.get('messages', []):
                conversation_history[user_id]["messages"].append({
                    "role": "assistant",
                    "content": message_text
                })
                await message.answer(message_text)
        else:
            # Если произошла ошибка, отправляем стандартное сообщение
            greeting_message = (
                "История диалога очищена.\n"
                "Я медицинский ассистент, созданный для помощи в предварительной диагностике. "
                "Пожалуйста, опишите, что вас беспокоит."
            )
            conversation_history[user_id]["messages"].append({
                "role": "assistant",
                "content": greeting_message
            })
            await message.answer(greeting_message)
    except Exception as e:
        bot_logger.error(f"Ошибка при обработке запроса: {str(e)}")
        greeting_message = (
            "История диалога очищена.\n"
            "Я медицинский ассистент, созданный для помощи в предварительной диагностике. "
            "Пожалуйста, опишите, что вас беспокоит."
        )
        conversation_history[user_id]["messages"].append({
            "role": "assistant",
            "content": greeting_message
        })
        await message.answer(greeting_message)
    
    save_conversation_history(conversation_history)

@dp.message()
async def handle_message(message: Message):
    """Обработчик текстовых сообщений"""
    user_id = str(message.from_user.id)
    user_message = message.text
    
    bot_logger.info(f"Получено новое сообщение от пользователя {user_id}")
    bot_logger.info(f"Текст сообщения: {user_message}")
    
    try:
        conversation_history = load_conversation_history()
        
        # Проверяем существование пользователя и корректность структуры данных
        if user_id not in conversation_history or not isinstance(conversation_history[user_id], dict):
            conversation_history[user_id] = create_user_session(user_id)
            is_start_dialog = True
            bot_logger.info(f"Создана новая сессия для пользователя {user_id}")
        else:
            # Проверяем наличие ключа messages
            if "messages" not in conversation_history[user_id]:
                conversation_history[user_id]["messages"] = []
            is_start_dialog = len(conversation_history[user_id]["messages"]) == 0
            bot_logger.info(f"Продолжение диалога с пользователем {user_id}")
            bot_logger.info(f"Текущий этап: {conversation_history[user_id].get('current_stage', 'SYMPTOMS')}")
        
        conversation_history[user_id]["messages"].append({
            "role": "user",
            "content": user_message
        })
        
        bot_logger.info("Отправка запроса к серверу")
        try:
            response = requests.post(
                'http://localhost:5000/check-uc',
                json={
                    'prompt': conversation_history[user_id]["messages"],
                    'user_id': user_id,
                    'is_start_dialog': is_start_dialog
                },
                stream=True
            )
            
            if response.status_code == 200:
                # Используем новую функцию для постепенной отправки сообщения
                full_response, conversation_state = await send_gradual_message(message, response)
                
                if full_response and conversation_state:
                    # Обновляем историю сообщений
                    conversation_history[user_id]["messages"].append({
                        "role": "assistant",
                        "content": full_response
                    })

                    # Обновляем состояние диалога
                    old_stage = conversation_history[user_id].get("current_stage")
                    new_stage = conversation_state.get("next_stage") or conversation_state.get("current_stage")
                    
                    conversation_history[user_id].update({
                        "current_stage": new_stage,
                        "symptoms": conversation_state["symptoms"],
                        "patient_info": conversation_state["patient_info"]
                    })

                    # Отправляем дополнительные сообщения только при смене этапа
                    if old_stage != new_stage:
                        additional_messages = conversation_state.get("messages", [])
                        for msg in additional_messages:
                            conversation_history[user_id]["messages"].append({
                                "role": "assistant",
                                "content": msg
                            })
                            await message.answer(msg)

                    save_conversation_history(conversation_history)
                    bot_logger.info(f"Обновлена сессия пользователя {user_id}")
                    bot_logger.info(f"Переход с этапа {old_stage} на {new_stage}")

                    if conversation_state["symptoms"]:
                        bot_logger.info(f"Найденные симптомы: {', '.join(conversation_state['symptoms'])}")
                    if conversation_state["patient_info"]["age"]:
                        bot_logger.info(f"Возраст пациента: {conversation_state['patient_info']['age']}")
            else:
                bot_logger.error(f"Ошибка сервера: {response.status_code}")
                await message.answer(
                    "Извините, произошла ошибка при обработке вашего запроса. "
                    "Пожалуйста, попробуйте позже."
                )
        except Exception as e:
            bot_logger.error(f"Ошибка при отправке запроса: {str(e)}")
            await message.answer(
                "Извините, произошла ошибка при обработке вашего запроса. "
                "Пожалуйста, попробуйте позже."
            )
    
    except Exception as e:
        bot_logger.error(f"Произошла ошибка: {str(e)}")
        await message.answer(
            "Извините, произошла ошибка при обработке вашего запроса. "
            "Пожалуйста, попробуйте позже."
        )


async def main():
    bot_logger.info("Запуск бота медицинского ассистента")
    if not os.path.exists(DATA_FILE):
        save_conversation_history({})
        bot_logger.info("Создан новый файл истории диалогов")
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
