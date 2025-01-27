from typing import List, Optional
from dataclasses import dataclass
import json
import os
import requests
from dotenv import load_dotenv

from logging_config import setup_logger

load_dotenv()
problem_logger = setup_logger('problem_info', 'API_LOGGING')

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
    symptoms_complete: bool = False

    def __post_init__(self):
        """Инициализация с дедупликацией симптомов"""
        self.symptoms = list(set(self.symptoms))

    def add_symptoms(self, new_symptoms: List[str]):
        """Добавляет симптомы и сбрасывает флаг завершения при новых симптомах"""
        if new_symptoms:
            combined = list(set(self.symptoms + new_symptoms))
            if len(combined) > len(self.symptoms):
                self.symptoms = combined
                self.symptoms_complete = False

    def extract_symptoms(self, messages: List[dict]) -> None:
        """Анализирует сообщения и обновляет симптомы и флаг завершения"""
        try:
            user_messages = " ".join([msg["content"] for msg in messages if msg["role"] == "user"])

            system_prompt = {
                "role": "system",
                "content": """Вы - медицинский ассистент. Проанализируйте сообщение пользователя и:
            1. Выделите все упомянутые симптомы (только медицинские состояния)
            2. Определите завершено ли описание симптомов
            
            Правила обработки:
            - Игнорируйте отрицания и предположения ("нет температуры", "может болеть голова")
            - Учитывайте только явно выраженные текущие симптомы (<2 недель)
            - Любые нерелевантные сообщения (не о симптомах) считайте незавершенным описанием
            - Симптомы в прошлом (>2 недель назад) не учитывать
            - Симптомы_complete=true ТОЛЬКО при:
              • явном указании на завершение ("всё", "это основные симптомы")
              • полном описании состояния без неопределенности
              • прямом утверждении об отсутствии симптомов
            - Во всех остальных случаях, включая нерелевантные ответы, вопросы и частичные описания - symptoms_complete=false
            
            Примеры обработки:
            
            Пример 1:
            Пользователь: "Какая сегодня погода?"
            Ответ: {"symptoms": [], "symptoms_complete": false}
            
            Пример 2:
            Пользователь: "Расскажи анекдот"
            Ответ: {"symptoms": [], "symptoms_complete": false}
            
            Пример 3:
            Пользователь: "Просто спросить хотел..."
            Ответ: {"symptoms": [], "symptoms_complete": false}
            
            Пример 4:
            Пользователь: "У меня всё хорошо, спасибо"
            Ответ: {"symptoms": [], "symptoms_complete": true}
            
            Пример 5:
            Пользователь: "Болит горло когда глотаю. Больше ничего не беспокоит"
            Ответ: {"symptoms": ["Боль при глотании"], "symptoms_complete": true}
            
            Пример 6:
            Пользователь: "Слабость и головокружение, но я не уверен..."
            Ответ: {"symptoms": ["Слабость", "Головокружение"], "symptoms_complete": false}
            
            Формат ответа ТОЛЬКО как JSON:
            {"symptoms": ["симптом1", ...], "symptoms_complete": true/false}"""
            }

            chat_messages = [
                system_prompt,
                {"role": "user", "content": user_messages}
            ]

            payload = {
                "model": "gpt-4o-mini",
                "messages": chat_messages,
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
                symptoms = list(set(result.get("symptoms", [])))
                complete = result.get("symptoms_complete", False)

                self.add_symptoms(symptoms)
                if complete:
                    self.symptoms_complete = True

                problem_logger.info(f"Обновленные симптомы: {self.symptoms}")
                problem_logger.info(f"Флаг завершения: {self.symptoms_complete}")
            else:
                problem_logger.error(f"Ошибка API: {response.status_code} - {response.text}")

        except Exception as e:
            problem_logger.error(f"Ошибка при извлечении симптомов: {str(e)}")