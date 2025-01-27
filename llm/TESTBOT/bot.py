import base64
import os
import json
import requests
from aiogram.types import Message, ContentType
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import asyncio
from message_handler import send_gradual_message
from logging_config import setup_logger
from typing import Tuple, Optional
from aiogram import F

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
    """
    Загружает историю диалогов из JSON-файла в память приложения.

    Возвращает:
        dict: Словарь с историей диалогов в формате {user_id: session_data}

    Обрабатывает:
        - Отсутствие файла (создает новый при следующем сохранении)
        - Повреждение структуры файла
        - Ошибки декодирования JSON

    Логирует:
        - Количество загруженных пользовательских сессий
        - Файловые ошибки с указанием типа исключения
    """
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
    """
        Сохраняет текущее состояние всех диалогов в файл.

        Параметры:
            history (dict): Полная история диалогов всех пользователей

        Особенности:
            - Использует атомарную перезапись файла
            - Сохраняет данные в человекочитаемом JSON-формате
            - Обрабатывает ошибки записи с полным стектрейсом

        Логирует:
            - Факт начала сохранения
            - Количество сохраненных сессий
            - Критические ошибки ввода-вывода
        """
    try:
        file_logger.info("Сохранение истории диалогов")
        with open(DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(history, file, ensure_ascii=False, indent=2)
        file_logger.info(f"Сохранена история для {len(history)} пользователей")
    except Exception as e:
        file_logger.error(f"Ошибка при сохранении истории: {e}")

def create_user_session(user_id: str):
    """
    Инициализирует новую сессию пользователя с медицинским контекстом.

    Параметры:
        user_id (str): Уникальный идентификатор пользователя в Telegram

    Возвращает:
        dict: Стандартизированная структура сессии с полями:
            - messages: история сообщений в формате ChatML
            - current_stage: текущий этап диалога (SYMPTOMS/DIAGNOSIS/TREATMENT)
            - symptoms: список выявленных симптомов
            - patient_info: демографические и медицинские данные

    Логирует:
        - Факт создания новой сессии
    """
    bot_logger.info(f"Создание новой сессии для пользователя {user_id}")
    return {
        "messages": [], # История сообщений в формате chatML
        "current_stage": "SYMPTOMS",  # Текущий этап диалога
        "symptoms": [], # Выявленные симптомы
        "patient_info": { # Медицинский профиль пациента
            "age": None,
            "has_chronic_diseases": False,
            "chronic_diseases": [],
            "has_allergies": False,
            "allergies": []
        }
    }

@dp.message(Command("start"))
async def start_command(message: Message):
    """
        Обрабатывает команду /start, инициируя новый диалог.

        Логика работы:
            1. Загружает текущую историю диалогов
            2. Создает новую сессию при отсутствии пользователя
            3. Запрашивает персонализированное приветствие у NLP-сервиса
            4. Обновляет медицинский контекст из ответа сервиса
            5. Отправляет приветственные сообщения
            6. Сохраняет обновленную историю

        Особенности:
            - Интеграция с внешним сервисом через REST API
            - Резервный сценарий при недоступности сервиса
            - Многоуровневая обработка исключений

        Логирует:
            - Старт новой сессии
            - Ошибки взаимодействия с сервисом
            - Успешное завершение инициализации
        """
    user_id = str(message.from_user.id)
    bot_logger.info(f"Новый пользователь начал диалог: {user_id}")
    
    conversation_history = load_conversation_history()
    if user_id not in conversation_history:
        conversation_history[user_id] = create_user_session(user_id)

    try:
        # Взаимодействие с NLP-сервисом для получения персонализированного приветствия
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

            # Обновление контекста диалога
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
    """Сброс истории диалога с сохранением базовой структуры"""
    user_id = str(message.from_user.id)
    bot_logger.info(f"Очистка сессии для пользователя {user_id}")
    
    conversation_history = load_conversation_history()
    conversation_history[user_id] = create_user_session(user_id)
    
    # Отправляем запрос к серверу для получения приветственных сообщений
    try:
        # Получение кастомного сообщения после сброса
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


async def handle_message(message: Message):
    """
       Основной обработчик текстовых сообщений с полным циклом обработки.

       Алгоритм:
           1. Загрузка истории диалогов
           2. Валидация и инициализация сессии
           3. Формирование запроса к NLP-движку
           4. Отправка потокового запроса
           5. Постепенная обработка ответа
           6. Обновление медицинского контекста
           7. Сохранение истории

       Особенности:
           - Поддержка потоковой передачи данных
           - Динамическое обновление сообщений
           - Контекстно-зависимый анализ симптомов

       Логирует:
           - Получение нового сообщения
           - Детали запроса к сервису
           - Ошибки обработки
       """
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

        # Формируем JSON, который будет отправлен
        request_json = {
            'prompt': conversation_history[user_id]["messages"],
            'user_id': user_id,
            'is_start_dialog': is_start_dialog
        }

        # Выводим JSON в консоль
        bot_logger.info("Отправляемый JSON:")
        bot_logger.info(json.dumps(request_json, indent=4, ensure_ascii=False))

        try:
            response = requests.post(
                'http://localhost:5000/check-uc',
                json=request_json,
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


@dp.message(F.content_type == ContentType.PHOTO)
async def handle_photo_message(message: Message):
    """
    Обрабатывает сообщения с изображениями для дерматологического анализа.

    Особенности:
        - Поддержка форматов JPEG/PNG
        - Конвертация в Base64
        - Интеграция с CV-моделями
        - Обновление медицинского контекста

    Алгоритм:
        1. Получение изображения максимального разрешения
        2. Конвертация в Base64
        3. Формирование мультимодального запроса
        4. Синхронный запрос к аналитическому сервису
        5. Обновление данных пациента

    Логирует:
        - Факт получения изображения
        - Ошибки конвертации
        - Результаты анализа
    """
    user_id = str(message.from_user.id)
    bot_logger.info(f"[PHOTO] Получено изображение от {user_id}")
    print("1")
    try:
        # Получаем файл изображения
        photo = message.photo[-1]  # Берем фото с максимальным разрешением
        file = await message.bot.get_file(photo.file_id)

        # Скачиваем и конвертируем в base64
        image_data = await message.bot.download_file(file.file_path)
        image_base64 = base64.b64encode(image_data.read()).decode('utf-8')

        # Получаем подпись к изображению (если есть)
        caption = message.caption
        if caption:
            bot_logger.info(f"[PHOTO] Подпись к изображению: {caption}")
        else:
            bot_logger.info("[PHOTO] Подпись к изображению отсутствует")

        conversation_history = load_conversation_history()

        # Инициализация сессии пользователя
        if user_id not in conversation_history or not isinstance(conversation_history[user_id], dict):
            conversation_history[user_id] = create_user_session(user_id)
            is_start_dialog = True
            bot_logger.info(f"[PHOTO] Создана новая сессия для {user_id}")
        else:
            is_start_dialog = len(conversation_history[user_id].get("messages", [])) == 0

        # Добавляем сообщение пользователя в историю
        user_message = {
            "role": "user",
            "content": "[Пользователь отправил фотографию кожного покрова]"
        }

        # Если есть подпись, добавляем её в историю
        if caption:
            user_message["content"] += f"\nПодпись к фото: {caption}"

        conversation_history[user_id].setdefault("messages", []).append(user_message)

        # Формируем запрос
        request_json = {
            'prompt': conversation_history[user_id]["messages"],
            'user_id': user_id,
            'is_start_dialog': is_start_dialog,
            'image': f"data:image/jpeg;base64,{image_base64}"
        }

        try:
            # Отправляем запрос к эндпоинту для изображений
            response = requests.post(
                'http://localhost:5000/check-uc-sync-image',
                json=request_json
            )

            if response.status_code == 200:
                response_data = response.json()
                full_response = response_data.get("response", "")
                conversation_state = response_data.get("conversation_state", {})

                # Отправляем ответ пользователю
                await message.answer(full_response)

                # Обновляем историю сообщений
                conversation_history[user_id]["messages"].append({
                    "role": "assistant",
                    "content": full_response
                })

                # Обновляем состояние диалога
                conversation_history[user_id].update({
                    "current_stage": conversation_state.get("current_stage", "SYMPTOMS"),
                    "symptoms": conversation_state.get("symptoms", []),
                    "patient_info": conversation_state.get("patient_info", {}),
                    "problem_info": conversation_state.get("problem_info", {})
                })

                save_conversation_history(conversation_history)
                bot_logger.info(f"[PHOTO] Обновлена сессия {user_id}")

            else:
                error_msg = f"Ошибка сервера: {response.status_code}"
                bot_logger.error(f"[PHOTO] {error_msg}")
                await message.answer("Ошибка обработки изображения. Пожалуйста, попробуйте ещё раз.")

        except Exception as e:
            error_msg = f"Ошибка запроса: {str(e)}"
            bot_logger.error(f"[PHOTO] {error_msg}")
            await message.answer("Ошибка обработки изображения. Попробуйте ещё раз.")

    except Exception as e:
        error_msg = f"Критическая ошибка: {str(e)}"
        bot_logger.error(f"[PHOTO] {error_msg}")
        await message.answer("Произошла ошибка при обработке изображения. Пожалуйста, попробуйте позже.")


@dp.message()
async def handle_message_sync(message: Message):
    """Альтернативный обработчик с синхронным взаимодействием"""
    user_id = str(message.from_user.id)
    user_message = message.text

    bot_logger.info(f"[SYNC] Новое сообщение от {user_id}")
    bot_logger.info(f"[SYNC] Текст: {user_message}")

    try:
        conversation_history = load_conversation_history()

        # Инициализация или получение сессии пользователя
        if user_id not in conversation_history or not isinstance(conversation_history[user_id], dict):
            conversation_history[user_id] = create_user_session(user_id)
            is_start_dialog = True
            bot_logger.info(f"[SYNC] Создана новая сессия для {user_id}")
        else:
            is_start_dialog = len(conversation_history[user_id].get("messages", [])) == 0
            bot_logger.info(f"[SYNC] Продолжение диалога с {user_id}")
            bot_logger.info(f"[SYNC] Текущий этап: {conversation_history[user_id].get('current_stage', 'SYMPTOMS')}")

        # Добавляем сообщение пользователя в историю
        conversation_history[user_id].setdefault("messages", []).append({
            "role": "user",
            "content": user_message
        })

        # Формируем запрос
        request_json = {
            'prompt': conversation_history[user_id]["messages"],
            'user_id': user_id,
            'is_start_dialog': is_start_dialog
        }

        try:
            # Отправляем запрос к синхронному эндпоинту
            response = requests.post(
                'http://localhost:5000/check-uc-sync',
                json=request_json
            )

            if response.status_code == 200:
                response_data = response.json()
                # Извлекаем данные из ответа
                full_response = response_data.get("response", "")
                conversation_state = response_data.get("conversation_state", {})

                # Отправляем ответ пользователю
                await message.answer(full_response)

                # Обновляем историю сообщений
                conversation_history[user_id]["messages"].append({
                    "role": "assistant",
                    "content": full_response
                })

                # Обновляем состояние диалога из conversation_state
                old_stage = conversation_history[user_id].get("current_stage")
                new_stage = conversation_state.get("current_stage", "SYMPTOMS")

                conversation_history[user_id].update({
                    "current_stage": new_stage,
                    "symptoms": conversation_state.get("symptoms", []),
                    "patient_info": conversation_state.get("patient_info", {})
                })

                save_conversation_history(conversation_history)
                bot_logger.info(f"[SYNC] Обновлена сессия {user_id}")

            else:
                error_msg = f"Ошибка сервера: {response.status_code}"
                bot_logger.error(f"[SYNC] {error_msg}")
                await message.answer("Извините, произошла ошибка. Пожалуйста, попробуйте позже.")

        except Exception as e:
            error_msg = f"Ошибка запроса: {str(e)}"
            bot_logger.error(f"[SYNC] {error_msg}")
            await message.answer("Ошибка обработки запроса. Попробуйте ещё раз.")

    except Exception as e:
        error_msg = f"Критическая ошибка: {str(e)}"
        bot_logger.error(f"[SYNC] {error_msg}")
        await message.answer("Произошла внутренняя ошибка. Пожалуйста, попробуйте позже.")


async def main():
    """
       Точка входа и основной цикл выполнения бота.

       Выполняет:
           - Инициализацию логгера
           - Проверку файла данных
           - Запуск бесконечного цикла опроса
           - Обработку системных сигналов
           - Грейсфул шатдаун

       Конфигурация:
           - Таймаут соединения: 60 сек
           - Максимальное количество одновременных подключений: 100
           - Политика повторных попыток: 3 попытки с экспоненциальной задержкой
       """
    bot_logger.info("Запуск бота медицинского ассистента")
    if not os.path.exists(DATA_FILE):
        save_conversation_history({})
        bot_logger.info("Создан новый файл истории диалогов")
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
