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
    """
      Класс для сбора и обработки информации о пациенте.

      Содержит методы для извлечения:
      - возраста
      - хронических заболеваний
      - аллергий

      А также проверки полноты собранной информации.
      """
    def __init__(self):
        """Инициализация с параметрами по умолчанию"""
        self.age: Optional[int] = None
        self.has_chronic_diseases: bool = True  # По умолчанию True
        self.chronic_diseases: List[str] = []
        self.has_allergies: bool = True  # По умолчанию True
        self.allergies: List[str] = []
        
    def to_dict(self) -> dict:
        """Сериализация данных пациента в словарь"""
        return {
            "age": self.age,
            "has_chronic_diseases": self.has_chronic_diseases,
            "chronic_diseases": self.chronic_diseases,
            "has_allergies": self.has_allergies,
            "allergies": self.allergies
        }
        
    def extract_age(self, message: str, prev_message: str = None) -> Optional[int]:
        """
        Извлечение возраста из текста сообщения с использованием GPT-модели.

        Args:
            message (str): Сообщение пользователя
            prev_message (str, optional): Предыдущее сообщение ассистента для контекста

        Returns:
            Optional[int]: Извлеченный возраст или None
        """
        try:
            patient_logger.info("=" * 50)
            patient_logger.info("Извлечение возраста:")
            patient_logger.info(f"Предыдущее сообщение ассистента: {prev_message}")
            patient_logger.info(f"Сообщение пользователя: {message}")

            # Системный промпт для модели с правилами обработки
            system_prompt = {
                "role": "system",
                "content": """Извлеките возраст пациента из сообщения. Правила:
            - Возвращайте только первое упомянутое целое число в диапазоне 0-120
            - Игнорируйте даты, годы рождения и косвенные указания ("молодой", "пожилой")
            - Если возраст не найден - возвращайте null
            
            Примеры:
            1. Сообщение: "Мне 25 лет" → {"age": 25}
            2. Сообщение: "Возраст 45" → {"age": 45}
            3. Сообщение: "Ребенку 5 годиков" → {"age": 5}
            4. Сообщение: "Родился в 1990" → {"age": null}
            5. Сообщение: "Два дня назад исполнилось 30" → {"age": 30}
            6. Сообщение: "Номер 45 не связан с возрастом" → {"age": null}
            7. Сообщение: "37.5 лет" → {"age": 37}
            8. Сообщение: "Младшему сыну 12, мне 40" → {"age": 40}
            9. Сообщение: "Возрастная группа 50-60 лет" → {"age": null}
            
            Формат: {"age": число или null}"""
            }
            
            patient_logger.info(f"Системный промпт для нейросети: {system_prompt['content']}")

            # Формирование списка сообщений для модели
            messages = [
                system_prompt,
                {"role": "assistant", "content": prev_message} if prev_message else None,
                {"role": "user", "content": message}
            ]

            messages = [msg for msg in messages if msg is not None]

            # Формирование тела запроса к API
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.1, # Низкая температура для точности
                "max_tokens": 50
            }

            # Отправка POST-запроса
            response = requests.post(
                PROXY_OPENAI_URL,
                headers=OPENAI_HEADERS,
                json=payload
            )

            # Обработка успешного ответа
            if response.status_code == 200:
                response_content = response.json()["choices"][0]["message"]["content"]
                patient_logger.info(f"Ответ нейросети: {response_content}")
                result = json.loads(response_content)
                age = result.get("age")

                # Обновление данных пациента
                if age is not None:
                    self.age = age
                    patient_logger.info(f"✓ Найден и сохранен возраст: {age}")
                else:
                    patient_logger.info("✗ Возраст не найден в сообщении")
                return age
            # Обработка ошибок API
            else:
                patient_logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            patient_logger.error(f"Ошибка при извлечении возраста: {str(e)}")
            return None
        
    def extract_chronic_diseases(self, message: str, prev_message: str = None) -> List[str]:
        """
        Извлекает хронические заболевания из сообщения пользователя.

        Алгоритм работы:
        1. Анализирует контекст предыдущего сообщения ассистента
        2. Определяет явные отрицания в ответ на прямой вопрос
        3. Использует GPT-модель для извлечения заболеваний
        4. Обновляет внутреннее состояние объекта

        Параметры:
            message (str): Текущее сообщение пользователя
            prev_message (str, optional): Последнее сообщение ассистента для контекста

        Возвращает:
            List[str]: Список новых извлеченных заболеваний (без дубликатов)

        Примеры сценариев:
            - "Нет хронических болезней" → очищает список
            - "Гипертония и диабет" → добавляет в список
            - "В детстве была астма" → игнорирует
        """
        try:
            patient_logger.info("=" * 50)
            patient_logger.info("Извлечение хронических заболеваний:")
            patient_logger.info(f"Предыдущее сообщение ассистента: {prev_message}")
            patient_logger.info(f"Сообщение пользователя: {message}")
            
            # Проверка на явное отрицание в контексте вопроса о заболеваниях
            if prev_message and any(phrase in prev_message.lower() for phrase in ["хронические заболевания", "хронических заболеваний"]):
                if any(phrase in message.lower() for phrase in ["нет", "нету", "отсутствуют", "не имею"]):
                    self.has_chronic_diseases = False
                    self.chronic_diseases = []
                    patient_logger.info("✓ Явно указано отсутствие хронических заболеваний в ответ на прямой вопрос")
                    return []
            else:
                patient_logger.info("Предыдущее сообщение не содержало вопроса о хронических заболеваниях")

            # Формирование системного промпта с правилами извлечения
            system_prompt = {
                "role": "system",
                "content": """Извлеките хронические заболевания. Правила:
            - Учитывайте только текущие заболевания с длительным течением
            - Игнорировать перенесенные в прошлом (>5 лет назад)
            - has_diseases=false ТОЛЬКО при явном отрицании
            
            Примеры:
            1. Сообщение: "Нет хронических болезней" → {"diseases": [], "has_diseases": false}
            2. Сообщение: "Гипертония и диабет 2 типа" → {"diseases": ["Гипертония", "Диабет 2 типа"], "has_diseases": true}
            3. Сообщение: "Раньше была астма" → {"diseases": [], "has_diseases": true}
            4. Сообщение: "Не имею хронических заболеваний" → {"diseases": [], "has_diseases": false}
            5. Сообщение: "Артрит с 2010 года" → {"diseases": ["Артрит"], "has_diseases": true}
            6. Сообщение: "Только аллергия на пыль" → {"diseases": [], "has_diseases": true}
            7. Сообщение: "ХБП 3 стадии" → {"diseases": ["Хроническая болезнь почек 3 стадии"], "has_diseases": true}
            8. Сообщение: "Хронических нет" → {"diseases": [], "has_diseases": false}
            9. Сообщение: "В детстве был ДЦП" → {"diseases": [], "has_diseases": true}
            
            Формат: {"diseases": ["болезнь1", ...], "has_diseases": true/false}"""
            }
            
            patient_logger.info(f"Системный промпт для нейросети: {system_prompt['content']}")

            # Подготовка сообщений для GPT-модели
            messages = [
                system_prompt,
                {"role": "assistant", "content": prev_message} if prev_message else None,
                {"role": "user", "content": message}
            ]
            
            # Убираем None из списка сообщений
            messages = [msg for msg in messages if msg is not None] # Очистка от None
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.1, # Низкая температура для точности
                "max_tokens": 100
            }

            # Отправка запроса к API
            response = requests.post(
                PROXY_OPENAI_URL,
                headers=OPENAI_HEADERS,
                json=payload
            )

            # Обработка успешного ответа
            if response.status_code == 200:
                response_content = response.json()["choices"][0]["message"]["content"]
                patient_logger.info(f"Ответ нейросети: {response_content}")
                result = json.loads(response_content)
                diseases = result.get("diseases", [])
                has_diseases = result.get("has_diseases", True)

                # Обновление состояния
                if not has_diseases:
                    self.has_chronic_diseases = False
                    self.chronic_diseases = []
                    patient_logger.info("✓ Определено отсутствие хронических заболеваний")
                    return []

                # Дедупликация и объединение списков
                if diseases:
                    self.has_chronic_diseases = True
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
        """
            Извлекает информацию об аллергиях из сообщения пользователя с использованием GPT-модели.

            Параметры:
                message (str): Текущее сообщение пользователя
                prev_message (str, optional): Последнее сообщение ассистента для контекста

            Возвращает:
                List[str]: Список новых обнаруженных аллергенов (без дубликатов)

            Логика работы:
                1. Проверяет контекст на прямой вопрос об аллергиях
                2. Определяет явное отрицание аллергий
                3. Использует GPT для извлечения аллергенов из текста
                4. Обновляет внутреннее состояние объекта
                5. Возвращает новые обнаруженные аллергены
            """
        try:
            patient_logger.info("=" * 50)
            patient_logger.info("Извлечение аллергий:")
            patient_logger.info(f"Предыдущее сообщение ассистента: {prev_message}")
            patient_logger.info(f"Сообщение пользователя: {message}")
            
            # Проверка контекста на вопрос об аллергиях
            if prev_message and any(phrase in prev_message.lower() for phrase in ["аллергии", "аллергия"]):
                # Поиск отрицательного ответа
                if any(phrase in message.lower() for phrase in ["нет", "нету", "отсутствуют", "не имею"]):
                    self.has_allergies = False
                    self.allergies = []
                    patient_logger.info("✓ Явно указано отсутствие аллергий в ответ на прямой вопрос")
                    return []
            else:
                patient_logger.info("Предыдущее сообщение не содержало вопроса об аллергиях")

            # Формирование системного промпта с правилами извлечения
            system_prompt = {
                "role": "system",
                "content": """Извлеките аллергические реакции. Правила:
            - Учитывайте только подтвержденные аллергии
            - has_allergies=false ТОЛЬКО при прямом отрицании
            - Непредоставление информации ≠ отрицание
            
            Примеры:
            1. Сообщение: "Нет аллергии" → {"allergies": [], "has_allergies": false}
            2. Сообщение: "На пенициллин и орехи" → {"allergies": ["Пенициллин", "Орехи"], "has_allergies": true}
            3. Сообщение: "Была сыпь на клубнику" → {"allergies": [], "has_allergies": true}
            4. Сообщение: "Не переносят пыльцу" → {"allergies": ["Пыльца"], "has_allergies": true}
            5. Сообщение: "Аллергий не имею" → {"allergies": [], "has_allergies": false}
            6. Сообщение: "Реакция на аспирин" → {"allergies": ["Аспирин"], "has_allergies": true}
            7. Сообщение: "Отсутствует аллергия" → {"allergies": [], "has_allergies": false}
            8. Сообщение: "Кошачья шерсть вызывает чихание" → {"allergies": ["Кошачья шерсть"], "has_allergies": true}
            9. Сообщение: "Не знаю, не проверялся" → {"allergies": [], "has_allergies": true}
            
            Формат: {"allergies": ["аллерген1", ...], "has_allergies": true/false}"""
            }
            
            patient_logger.info(f"Системный промпт для нейросети: {system_prompt['content']}")

            # Подготовка списка сообщений для модели
            messages = [
                system_prompt,
                {"role": "assistant", "content": prev_message} if prev_message else None,
                {"role": "user", "content": message}
            ]
            
            # Фильтрация None-значений
            messages = [msg for msg in messages if msg is not None]

            # Формирование тела запроса
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 100
            }

            # Отправка запроса к API
            response = requests.post(
                PROXY_OPENAI_URL,
                headers=OPENAI_HEADERS,
                json=payload
            )

            # Обработка успешного ответа
            if response.status_code == 200:
                response_content = response.json()["choices"][0]["message"]["content"]
                patient_logger.info(f"Ответ нейросети: {response_content}")
                result = json.loads(response_content)
                allergies = result.get("allergies", [])
                has_allergies = result.get("has_allergies", True)

                # Обновление состояния аллергий
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
        """
        Проверка полноты информации о пациенте.

        Returns:
            bool: True если все обязательные поля заполнены:
                - Возраст указан
                - При наличии хронических заболеваний - заполнен список
                - При наличии аллергий - заполнен список
        """
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