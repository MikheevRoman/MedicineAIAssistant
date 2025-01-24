from typing import List, Optional
from dataclasses import dataclass
import json
import os
import requests
from dotenv import load_dotenv

from logging_config import setup_logger

load_dotenv()

# Инициализация логгера
problem_logger = setup_logger('problem_info', 'API_LOGGING')

# Настройки API
PROXY_API_KEY = os.getenv('PROXY_API_KEY')
PROXY_OPENAI_URL = "https://api.proxyapi.ru/openai/v1/chat/completions"

OPENAI_HEADERS = {
    "Authorization": f"Bearer {PROXY_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "text/event-stream"
}

@dataclass
class ProblemInfo:
    symptoms: List[str]
    duration: Optional[str] = None
    severity: Optional[str] = None

    def __post_init__(self):
        """Удаляем дубликаты при инициализации"""
        self.symptoms = list(set(self.symptoms))

    def add_symptoms(self, new_symptoms: List[str]):
        """Добавляет новые симптомы с дедупликацией"""
        self.symptoms = list(set(self.symptoms + new_symptoms))

    @staticmethod
    def extract_symptoms(messages: List[dict]) -> List[str]:
        """Извлекает симптомы из сообщения пользователя"""
        try:
            # Собираем все сообщения пользователя в один текст
            user_messages = " ".join([msg["content"] for msg in messages if msg["role"] == "user"])
            
            system_prompt = {
                "role": "system",
                "content": "Вы - медицинский ассистент. Проанализируйте сообщение пользователя и выделите все упомянутые "
                          "симптомы. Верните их списком в формате JSON: {\"symptoms\": [\"симптом1\", \"симптом2\"]}"
            }
            
            messages = [
                system_prompt,
                {"role": "user", "content": user_messages}
            ]
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 200
            }
            
            response = requests.post(
                PROXY_OPENAI_URL,
                headers=OPENAI_HEADERS,
                json=payload
            )
            
            if response.status_code == 200:
                result = json.loads(response.json()["choices"][0]["message"]["content"])
                symptoms = list(set(result.get("symptoms", [])))  # Дедупликация при извлечении
                problem_logger.info(f"Извлечены симптомы: {symptoms}")
                return symptoms
            else:
                problem_logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                return []
            
        except Exception as e:
            problem_logger.error(f"Ошибка при извлечении симптомов: {str(e)}")
            return [] 