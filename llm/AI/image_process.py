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
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string


def generate_from_image(image_path):
    base64_image = encode_image_to_base64(image_path)

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
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
                "role": "user",
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
        "max_tokens": 100,
        "temperature": 0.7,
        "stream": True,
    }

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
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data: "):
                data = json.loads(decoded_line[len("data: "):])
                if "choices" in data and data["choices"]:
                    content = data["choices"][0]["delta"].get("content", "")
                    if content:
                        yield content
            if decoded_line == "data: [DONE]":
                break
        except Exception as e:
            continue
