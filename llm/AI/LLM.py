import json
import requests
from dotenv import load_dotenv
from flask import Flask, request, Response, stream_with_context
from openai import OpenAI
import os
import logging
from embeddings_handler import CustomEmbeddings
from pdf_processor import load_and_process_pdfs
from context_manager import get_relevant_context
from logger_config import setup_logger

setup_logger()
logger = logging.getLogger('llm')

load_dotenv()

app = Flask(__name__)

PROXY_API_KEY = os.getenv('PROXY_API_KEY')
PROXY_OPENAI_URL = "https://api.proxyapi.ru/openai/v1/chat/completions"

OPENAI_HEADERS = {
    "Authorization": f"Bearer {PROXY_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "text/event-stream"
}

client = OpenAI(
    api_key=f"{os.getenv('PROXY_API_KEY')}",
    base_url="https://api.proxyapi.ru/openai/v1/chat/completions",
)

# Инициализация
embeddings = CustomEmbeddings()
vector_stores = load_and_process_pdfs()

@app.route('/check-uc', methods=['POST'])
def process_data():
    data = request.get_json()
    messages = data.get('prompt', [])
    
    logger.info(f"Получен новый запрос с {len(messages)} сообщениями")
    
    last_user_message = next((msg['content'] for msg in reversed(messages) 
                            if msg['role'] == 'user'), '')
    
    logger.info("Получение релевантного контекста из базы знаний")
    context = get_relevant_context(last_user_message, vector_stores)
    logger.info("Контекст успешно получен")

    system_message = {
        "role": "system",
        "content": (
            "Вы - медицинский ассистент, который помогает определить предварительный диагноз и направить пациента "
            "к соответствующему специалисту. Используйте предоставленную информацию из медицинской литературы для "
            "формирования более точных ответов. Ваши основные задачи:\n\n"
            "1. Всегда общаться на русском языке\n"
            "2. Задавать уточняющие вопросы о симптомах, их длительности и характере\n"
            "3. Собрать важную информацию о: возрасте пациента, наличии хронических заболеваний, аллергий\n"
            "4. После получения достаточной информации:\n"
            "   - Предложить предварительный диагноз\n"
            "   - Указать к какому специалисту нужно обратиться\n"
            "   - Если ситуация экстренная, обязательно рекомендовать немедленно обратиться за медицинской помощью\n\n"
            "ВАЖНО: Всегда подчеркивать, что это предварительная консультация, и окончательный диагноз может поставить "
            "только врач при очном осмотре. При опасных симптомах настоятельно рекомендовать немедленно обратиться к врачу "
            "или вызвать скорую помощь.\n\n"
            f"{context}"
        )
    }
    
    full_messages = [system_message] + messages

    def generate():
        payload = {
            "model": "gpt-4o-mini",
            "messages": full_messages,
            "max_tokens": 5000,
            "temperature": 0.7,
            "stream": True,
        }

        logger.info("Отправка запроса к OpenAI API")
        response = requests.post(
            PROXY_OPENAI_URL,
            headers=OPENAI_HEADERS,
            json=payload,
            stream=True
        )

        if response.status_code != 200:
            logger.error(f"Ошибка API OpenAI: {response.status_code}")
            yield f"data: {json.dumps({'error': 'OpenAI API Error'})}\n\n"
            return

        for line in response.iter_lines():
            if not line:
                continue
            
            try:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    yield f"{decoded_line}\n"
                if decoded_line == "data: [DONE]":
                    logger.info("Генерация ответа завершена")
                    break
            except Exception as e:
                logger.error(f"Ошибка при обработке строки: {e}")
                continue

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    logger.info("Запуск сервера медицинского ассистента")
    app.run(host='0.0.0.0', port=5000)