from typing import List, Optional
import json
import os
import requests
from dotenv import load_dotenv

from logging_config import setup_logger

load_dotenv()

# Инициализация логгера
patient_logger = setup_logger('patient_info', 'API_LOGGING')

# Настройки API
PROXY_API_KEY = os.getenv('PROXY_API_KEY')
PROXY_OPENAI_URL = "https://api.proxyapi.ru/openai/v1/chat/completions"

OPENAI_HEADERS = {
    "Authorization": f"Bearer {PROXY_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "text/event-stream"
}

class PatientInfo:
    def __init__(self):
        self.age: Optional[int] = None
        self.has_chronic_diseases: bool = True  # По умолчанию True
        self.chronic_diseases: List[str] = []
        self.has_allergies: bool = True  # По умолчанию True
        self.allergies: List[str] = []
        
    def to_dict(self) -> dict:
        """Преобразует информацию о пациенте в словарь"""
        return {
            "age": self.age,
            "has_chronic_diseases": self.has_chronic_diseases,
            "chronic_diseases": self.chronic_diseases,
            "has_allergies": self.has_allergies,
            "allergies": self.allergies
        }
        
    def extract_age(self, message: str, prev_message: str = None) -> Optional[int]:
        """Извлекает возраст из сообщения пользователя"""
        try:
            patient_logger.info("=" * 50)
            patient_logger.info("Извлечение возраста:")
            patient_logger.info(f"Предыдущее сообщение ассистента: {prev_message}")
            patient_logger.info(f"Сообщение пользователя: {message}")
            
            system_prompt = {
                "role": "system",
                "content": "Найдите возраст пациента в сообщении пользователя и верните только число. "
                          "Предыдущее сообщение ассистента предоставлено только для понимания контекста диалога "
                          "и не должно влиять на поиск возраста. "
                          "Если возраст не указан в сообщении пользователя, верните null. "
                          "Формат: {\"age\": number or null}"
            }
            
            patient_logger.info(f"Системный промпт для нейросети: {system_prompt['content']}")
            
            messages = [
                system_prompt,
                {"role": "assistant", "content": prev_message} if prev_message else None,
                {"role": "user", "content": message}
            ]
            
            # Убираем None из списка сообщений
            messages = [msg for msg in messages if msg is not None]
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 50
            }
            
            response = requests.post(
                PROXY_OPENAI_URL,
                headers=OPENAI_HEADERS,
                json=payload
            )
            
            if response.status_code == 200:
                response_content = response.json()["choices"][0]["message"]["content"]
                patient_logger.info(f"Ответ нейросети: {response_content}")
                result = json.loads(response_content)
                age = result.get("age")
                
                if age is not None:
                    self.age = age
                    patient_logger.info(f"✓ Найден и сохранен возраст: {age}")
                else:
                    patient_logger.info("✗ Возраст не найден в сообщении")
                return age
            else:
                patient_logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            patient_logger.error(f"Ошибка при извлечении возраста: {str(e)}")
            return None
        
    def extract_chronic_diseases(self, message: str, prev_message: str = None) -> List[str]:
        """Извлекает хронические заболевания из сообщения пользователя"""
        try:
            patient_logger.info("=" * 50)
            patient_logger.info("Извлечение хронических заболеваний:")
            patient_logger.info(f"Предыдущее сообщение ассистента: {prev_message}")
            patient_logger.info(f"Сообщение пользователя: {message}")
            
            # Проверяем на явное отрицание с учетом контекста
            if prev_message and any(phrase in prev_message.lower() for phrase in ["хронические заболевания", "хронических заболеваний"]):
                if any(phrase in message.lower() for phrase in ["нет", "нету", "отсутствуют", "не имею"]):
                    self.has_chronic_diseases = False
                    self.chronic_diseases = []
                    patient_logger.info("✓ Явно указано отсутствие хронических заболеваний в ответ на прямой вопрос")
                    return []
            else:
                patient_logger.info("Предыдущее сообщение не содержало вопроса о хронических заболеваниях")

            system_prompt = {
                "role": "system",
                "content": "Найдите все упомянутые хронические заболевания в сообщении пользователя. "
                          "Предыдущее сообщение ассистента предоставлено только для понимания контекста диалога "
                          "и не должно влиять на поиск заболеваний. "
                          "Если явно указано что их нет (например, 'нет', 'не имею', 'отсутствуют'), верните пустой список и has_diseases: false. "
                          "Если нет явного указания на отсутствие заболеваний, оставьте has_diseases: true. "
                          "Формат: {\"diseases\": [\"заболевание1\", \"заболевание2\"], \"has_diseases\": boolean}"
            }
            
            patient_logger.info(f"Системный промпт для нейросети: {system_prompt['content']}")
            
            messages = [
                system_prompt,
                {"role": "assistant", "content": prev_message} if prev_message else None,
                {"role": "user", "content": message}
            ]
            
            # Убираем None из списка сообщений
            messages = [msg for msg in messages if msg is not None]
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 100
            }
            
            response = requests.post(
                PROXY_OPENAI_URL,
                headers=OPENAI_HEADERS,
                json=payload
            )
            
            if response.status_code == 200:
                response_content = response.json()["choices"][0]["message"]["content"]
                patient_logger.info(f"Ответ нейросети: {response_content}")
                result = json.loads(response_content)
                diseases = result.get("diseases", [])
                has_diseases = result.get("has_diseases", True)
                
                if not has_diseases:
                    self.has_chronic_diseases = False
                    self.chronic_diseases = []
                    patient_logger.info("✓ Определено отсутствие хронических заболеваний")
                    return []
                
                if diseases:
                    self.has_chronic_diseases = True
                    old_diseases = set(self.chronic_diseases)
                    self.chronic_diseases = list(set(self.chronic_diseases + diseases))
                    patient_logger.info(f"✓ Найдены хронические заболевания: {diseases}")
                    patient_logger.info(f"✓ Обновленный список заболеваний: {self.chronic_diseases}")
                else:
                    patient_logger.info("✗ Хронические заболевания не упомянуты в сообщении")
                return diseases
            else:
                patient_logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                return []
            
        except Exception as e:
            patient_logger.error(f"Ошибка при извлечении хронических заболеваний: {str(e)}")
            return []
        
    def extract_allergies(self, message: str, prev_message: str = None) -> List[str]:
        """Извлекает аллергии из сообщения пользователя"""
        try:
            patient_logger.info("=" * 50)
            patient_logger.info("Извлечение аллергий:")
            patient_logger.info(f"Предыдущее сообщение ассистента: {prev_message}")
            patient_logger.info(f"Сообщение пользователя: {message}")
            
            # Проверяем на явное отрицание с учетом контекста
            if prev_message and any(phrase in prev_message.lower() for phrase in ["аллергии", "аллергия"]):
                if any(phrase in message.lower() for phrase in ["нет", "нету", "отсутствуют", "не имею"]):
                    self.has_allergies = False
                    self.allergies = []
                    patient_logger.info("✓ Явно указано отсутствие аллергий в ответ на прямой вопрос")
                    return []
            else:
                patient_logger.info("Предыдущее сообщение не содержало вопроса об аллергиях")

            system_prompt = {
                "role": "system",
                "content": "Найдите все упомянутые аллергии в сообщении пользователя. "
                          "Предыдущее сообщение ассистента предоставлено только для понимания контекста диалога "
                          "и не должно влиять на поиск аллергий. "
                          "Если явно указано что их нет (например, 'нет', 'не имею', 'отсутствуют'), верните пустой список и has_allergies: false. "
                          "Если нет явного указания на отсутствие аллергий, оставьте has_allergies: true. "
                          "Формат: {\"allergies\": [\"аллергия1\", \"аллергия2\"], \"has_allergies\": boolean}"
            }
            
            patient_logger.info(f"Системный промпт для нейросети: {system_prompt['content']}")
            
            messages = [
                system_prompt,
                {"role": "assistant", "content": prev_message} if prev_message else None,
                {"role": "user", "content": message}
            ]
            
            # Убираем None из списка сообщений
            messages = [msg for msg in messages if msg is not None]
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 100
            }
            
            response = requests.post(
                PROXY_OPENAI_URL,
                headers=OPENAI_HEADERS,
                json=payload
            )
            
            if response.status_code == 200:
                response_content = response.json()["choices"][0]["message"]["content"]
                patient_logger.info(f"Ответ нейросети: {response_content}")
                result = json.loads(response_content)
                allergies = result.get("allergies", [])
                has_allergies = result.get("has_allergies", True)
                
                if not has_allergies:
                    self.has_allergies = False
                    self.allergies = []
                    patient_logger.info("✓ Определено отсутствие аллергий")
                    return []
                
                if allergies:
                    self.has_allergies = True
                    old_allergies = set(self.allergies)
                    self.allergies = list(set(self.allergies + allergies))
                    patient_logger.info(f"✓ Найдены аллергии: {allergies}")
                    patient_logger.info(f"✓ Обновленный список аллергий: {self.allergies}")
                else:
                    patient_logger.info("✗ Аллергии не упомянуты в сообщении")
                return allergies
            else:
                patient_logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                return []
            
        except Exception as e:
            patient_logger.error(f"Ошибка при извлечении аллергий: {str(e)}")
            return []

    def is_complete(self) -> bool:
        """Проверяет, заполнена ли вся информация о пациенте"""
        complete = (
            self.age is not None  # Возраст указан
            and (
                (not self.has_chronic_diseases)  # Явно указано отсутствие хронических заболеваний
                or (self.has_chronic_diseases and len(self.chronic_diseases) > 0)  # Или есть список заболеваний
            )
            and (
                (not self.has_allergies)  # Явно указано отсутствие аллергий
                or (self.has_allergies and len(self.allergies) > 0)  # Или есть список аллергий
            )
        )
        patient_logger.info(f"Проверка полноты информации: {complete}")
        return complete 