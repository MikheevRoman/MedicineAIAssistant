import base64
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

PROXY_API_KEY = os.getenv('PROXY_API_KEY')
PROXY_OPENAI_URL = "https://api.proxyapi.ru/openai/v1/chat/completions"

OPENAI_HEADERS = {
    "Authorization": f"Bearer {PROXY_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "text/event-stream"
}


def encode_image_to_base64(image_path):
    """
        Кодирует изображение в формате Base64.

        Аргументы:
        - image_path: Путь к изображению.

        Возвращает:
        - Строку с закодированным изображением в формате Base64.
        """
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string


def generate_from_image(image_path):
    """
    Отправляет изображение в Proxy OpenAI API для анализа кожных проблем.

    Аргументы:
    - image_path: Путь к изображению.

    Возвращает:
    - Генератор, который итерирует текстовый ответ от API.
    """
    # Кодирование изображения в Base64
    base64_image = encode_image_to_base64(image_path)

    # Подготовка JSON-пейлоада для запроса
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system", # Сообщение от системы с инструкцией для модели
                "content": [
                    {
                        "type": "text",
                        "text": """Твоя задача — вывести пользователю список кожных проблем, обнаруженных на изображении, в формате списка в квадратных скобках, на русском языке. 
Пример ответа, если проблемы есть: [покраснение, прыщ, сыпь]
Если проблем нет, верни [].
Ответ должен быть исключительно списком в квадратных скобках — никаких пояснений."""
                    }
                ]
            },
            {
                "role": "user", # Сообщение от пользователя с изображением
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "low"
                        }
                    },
                ]
            }
        ],
        "max_tokens": 100, # Максимальное количество токенов в ответе
        "temperature": 0.7, # Параметр креативности модели
        "stream": True, # Указание на использование потоковой передачи данных
    }

    # Отправка POST-запроса к Proxy API
    response = requests.post(
        PROXY_OPENAI_URL,
        headers=OPENAI_HEADERS,
        json=payload,
        stream=True
    )

    if response.status_code != 200:
        yield f"data: {json.dumps({'error': 'OpenAI API Error'})}\n\n"
        return

    for line in response.iter_lines():
        if not line:
            continue

        try:
            decoded_line = line.decode('utf-8') # Декодирование строки из байтов в текст
            if decoded_line.startswith("data: "): # Проверка, содержит ли строка данные
                data = json.loads(decoded_line[len("data: "):]) # Парсинг JSON-данных
                if "choices" in data and data["choices"]: # Проверка наличия данных в ответе
                    content = data["choices"][0]["delta"].get("content", "")  # Извлечение содержимого ответа
                    if content:
                        yield content # Отправка данных через генератор
            if decoded_line == "data: [DONE]": # Условие завершения потока
                break
        except Exception as e:
            continue
