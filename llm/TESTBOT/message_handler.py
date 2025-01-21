import logging
from typing import Dict, Any
import json
import asyncio

logger = logging.getLogger('message_handler')

BUFFER_SIZE = 50

async def process_stream_response(response_line: str) -> Dict[str, Any]:
    """Обрабатывает строку ответа от сервера"""
    try:
        if response_line.startswith("data: "):
            data = json.loads(response_line[6:])
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {e}")
    return {}

async def send_gradual_message(message, response):
    """Отправляет сообщение постепенно, по мере получения данных"""
    try:
        logger.info("Начало отправки постепенного сообщения")
        partial_message = ""
        message_id = None
        update_buffer = ""

        for line in response.iter_lines():
            if not line:
                continue

            # Даем возможность другим корутинам выполняться
            await asyncio.sleep(0)

            decoded_line = line.decode('utf-8')
            chunk = await process_stream_response(decoded_line)

            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {}).get("content", "")
                if delta:
                    update_buffer += delta
                    if len(update_buffer) >= BUFFER_SIZE:
                        partial_message += update_buffer
                        update_buffer = ""
                        if message_id is None:
                            sent_message = await message.answer(partial_message)
                            message_id = sent_message.message_id
                        else:
                            await message.bot.edit_message_text(
                                chat_id=message.chat.id,
                                message_id=message_id,
                                text=partial_message
                            )

        # Отправляем оставшийся текст
        if update_buffer:
            partial_message += update_buffer
            if message_id is None:
                await message.answer(partial_message)
            else:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message_id,
                    text=partial_message
                )
        
        return partial_message

    except Exception as e:
        logger.error(f"Ошибка при отправке постепенного сообщения: {e}")
        await message.answer(
            "Извините, произошла ошибка при отправке сообщения. "
            "Пожалуйста, попробуйте позже."
        )
        return None 