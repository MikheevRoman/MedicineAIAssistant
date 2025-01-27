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
    """
    Класс для работы с информацией о симптомах и проблеме пациента.

    Атрибуты:
    - symptoms (List[str]): список выявленных симптомов
    - duration (Optional[str]): продолжительность симптомов (если указано)
    - severity (Optional[str]): тяжесть состояния (если указано)
    - symptoms_complete (bool): флаг завершенности описания симптомов
    """
    symptoms: List[str]
    duration: Optional[str] = None
    severity: Optional[str] = None
    symptoms_complete: bool = False

    def __post_init__(self):
        """Инициализация с дедупликацией симптомов"""
        self.symptoms = list(set(self.symptoms))

    def add_symptoms(self, new_symptoms: List[str]):
        """
        Добавляет новые симптомы к текущему списку.

        Если список симптомов обновляется, флаг завершенности сбрасывается.
        """
        if new_symptoms:
            combined = list(set(self.symptoms + new_symptoms))
            if len(combined) > len(self.symptoms):
                self.symptoms = combined
                self.symptoms_complete = False

    def extract_symptoms(self, messages: List[dict]) -> None:
        """
        Анализирует сообщения пользователя для выявления симптомов.

        Использует GPT-модель для:
        1. Извлечения медицинских симптомов
        2. Определения полноты описания симптомов
        """
        try:
            # Объединяем все сообщения пользователя в одну строку
            user_messages = " ".join([msg["content"] for msg in messages if msg["role"] == "user"])

            # Системное сообщение с инструкциями для модели
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

            # Формируем список сообщений для модели
            chat_messages = [
                system_prompt, # Системное сообщение с инструкцией
                {"role": "user", "content": user_messages} # Сообщение пользователя
            ]

            # Формируем payload для запроса к API
            payload = {
                "model": "gpt-4o-mini",  # Выбранная модель
                "messages": chat_messages,
                "temperature": 0.1,      # Низкая температура для минимальной вариативности
                "max_tokens": 200        # Ограничение на количество токенов в ответе
            }

            # Отправляем POST-запрос к API
            response = requests.post(
                PROXY_OPENAI_URL,
                headers=OPENAI_HEADERS,
                json=payload
            )

            # Обработка успешного ответа
            if response.status_code == 200:
                result = json.loads(response.json()["choices"][0]["message"]["content"])
                symptoms = list(set(result.get("symptoms", []))) # Получаем список симптомов
                complete = result.get("symptoms_complete", False) # Получаем флаг завершенности

                # Обновляем симптомы и флаг завершенности
                self.add_symptoms(symptoms)
                if complete:
                    self.symptoms_complete = True

                problem_logger.info(f"Обновленные симптомы: {self.symptoms}")
                problem_logger.info(f"Флаг завершения: {self.symptoms_complete}")
            else:
                problem_logger.error(f"Ошибка API: {response.status_code} - {response.text}")

        except Exception as e:
            problem_logger.error(f"Ошибка при извлечении симптомов: {str(e)}")