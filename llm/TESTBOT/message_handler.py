from typing import Dict, Any, Tuple, Optional
import json
import asyncio
from logging_config import setup_logger

# Инициализация логгеров
msg_logger = setup_logger('message_handler', 'API_LOGGING')

BUFFER_SIZE = 50 # Оптимальный размер буфера для баланса между отзывчивостью и нагрузкой

async def process_stream_response(response_line: str) -> Dict[str, Any]:
    """Парсит и валидирует строку ответа от сервера.

    Args:
        response_line (str): Строка ответа в формате Server-Sent Events (SSE)

    Returns:
        Dict: Распарсенные данные или пустой словарь при ошибке

    Обрабатывает:
        - JSON декодинг
        - Проверку формата данных
        - Различные типы ошибок с детальным логированием
    """
    try:
        if response_line.startswith("data: "):
            data = json.loads(response_line[6:])
            if not isinstance(data, dict):
                msg_logger.warning(f"Некорректный формат данных: {data}")
                return {}
            return data
    except json.JSONDecodeError as e:
        msg_logger.error(f"Ошибка декодирования JSON: {e}")
    except Exception as e:
        msg_logger.error(f"Неожиданная ошибка при обработке ответа: {e}")
    return {}

async def send_gradual_message(message, response) -> Tuple[Optional[str], Optional[Dict]]:
    """Постепенная отправка сообщения с динамическим обновлением контента.

    Args:
        message: Объект сообщения от телеграм-библиотеки
        response: Асинхронный ответ сервера

    Returns:
        Tuple: (финальный текст сообщения, состояние диалога) или (None, None)

    Особенности:
        - Построчное чтение потокового ответа
        - Буферизация вывода для снижения нагрузки
        - Динамическое редактирование сообщения
        - Сохранение состояния диалога
    """
    try:
        msg_logger.info("Начало отправки постепенного сообщения")
        partial_message = ""      # Аккумулируемый текст ответа
        message_id = None         # Идентификатор сообщения в Telegram
        update_buffer = ""        # Буфер для накопления фрагментов
        conversation_state = None # Состояние диалога от LLM

        # Асинхронная обработка потокового ответа
        for line in response.iter_lines():
            if not line:
                continue

            try:
                # Кооперативная многозадачность - передача управления
                await asyncio.sleep(0)

                decoded_line = line.decode('utf-8')
                chunk = await process_stream_response(decoded_line)

                if not chunk:
                    continue

                # Обработка состояния диалога
                if "conversation_state" in chunk:
                    conversation_state = chunk["conversation_state"]
                    if isinstance(conversation_state, dict):
                        msg_logger.info(f"Получено состояние диалога: {conversation_state}")
                    else:
                        msg_logger.warning("Некорректный формат состояния диалога")
                        conversation_state = None
                    continue
            except Exception as e:
                msg_logger.error(f"Ошибка при обработке строки ответа: {e}")
                continue

            # Извлечение контента из чанка
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {}).get("content", "")
                if delta:
                    update_buffer += delta
                    if len(update_buffer) >= BUFFER_SIZE:
                        partial_message += update_buffer
                        update_buffer = ""

                        # Логика отправки/обновления сообщения
                        if message_id is None:
                            msg_logger.info("Отправка первой части сообщения")
                            sent_message = await message.answer(partial_message)
                            message_id = sent_message.message_id
                        else:
                            msg_logger.info("Обновление существующего сообщения")
                            await message.bot.edit_message_text(
                                chat_id=message.chat.id,
                                message_id=message_id,
                                text=partial_message
                            )

        # Отправка остатков из буфера
        if update_buffer:
            partial_message += update_buffer
            if message_id is None:
                msg_logger.info("Отправка единственного сообщения")
                await message.answer(partial_message)
            else:
                msg_logger.info("Отправка финального обновления")
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message_id,
                    text=partial_message
                )
        
        msg_logger.info(f"Отправка сообщения завершена. Длина сообщения: {len(partial_message)}")
        return partial_message, conversation_state

    except Exception as e:
        msg_logger.error(f"Ошибка при отправке постепенного сообщения: {e}")
        await message.answer(
            "Извините, произошла ошибка при отправке сообщения. "
            "Пожалуйста, попробуйте позже."
        )
        return None, None 