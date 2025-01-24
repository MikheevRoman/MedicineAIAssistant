from typing import List, Optional
from dataclasses import dataclass
from enum import Enum
from logging_config import setup_logger

# Инициализация логгеров
conv_logger = setup_logger('conversation', 'CONVERSATION_LOGGING')
api_logger = setup_logger('conversation_api', 'API_LOGGING')

class ConversationStage(Enum):
    SYMPTOMS = 1
    PATIENT_INFO = 2
    DIAGNOSIS = 3

@dataclass
class ProblemInfo:
    symptoms: List[str]
    duration: Optional[str] = None
    severity: Optional[str] = None

    @staticmethod
    def extract_symptoms(messages: List[dict]) -> List[str]:
        """Извлекает симптомы из сообщения пользователя"""
        system_prompt = {
            "role": "system",
            "content": "Вы - медицинский ассистент. Проанализируйте сообщение пользователя и выделите все упомянутые "
                      "симптомы. Верните их списком в формате JSON: {\"symptoms\": [\"симптом1\", \"симптом2\"]}"
        }
        return []

class PatientInfo:
    def __init__(self):
        self.age: Optional[int] = None
        self.has_chronic_diseases: bool = True
        self.chronic_diseases: List[str] = []
        self.has_allergies: bool = True
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
        
    def extract_age(self, message: str) -> Optional[int]:
        """Извлекает возраст из сообщения пользователя"""
        system_prompt = {
            "role": "system",
            "content": "Найдите возраст пациента в сообщении и верните только число. "
                      "Если возраст не указан, верните null. Формат: {\"age\": number or null}"
        }
        # Здесь будет вызов GPT API
        return None
        
    def extract_chronic_diseases(self, message: str) -> List[str]:
        """Извлекает хронические заболевания из сообщения пользователя"""
        system_prompt = {
            "role": "system",
            "content": "Найдите все упомянутые хронические заболевания. "
                      "Если явно указано что их нет, верните пустой список. "
                      "Формат: {\"diseases\": [\"заболевание1\", \"заболевание2\"]}"
        }
        # Здесь будет вызов GPT API
        return []
        
    def extract_allergies(self, message: str) -> List[str]:
        """Извлекает аллергии из сообщения пользователя"""
        system_prompt = {
            "role": "system",
            "content": "Найдите все упомянутые аллергии. "
                      "Если явно указано что их нет, верните пустой список. "
                      "Формат: {\"allergies\": [\"аллергия1\", \"аллергия2\"]}"
        }
        # Здесь будет вызов GPT API
        return []

    def is_complete(self) -> bool:
        """Проверяет, заполнена ли вся информация о пациенте"""
        return (
                self.age is not None
                and (self.has_chronic_diseases is False or (
                    self.has_chronic_diseases is True and len(self.chronic_diseases) > 0))
                and (self.has_allergies is False or (self.has_allergies is True and len(self.allergies) > 0))
        )


class ConversationManager:
    _instances = {}  # Словарь для хранения экземпляров менеджера для каждого пользователя

    @classmethod
    def get_instance(cls, user_id: str, is_start_dialog: bool = False):
        """Получает или создает экземпляр менеджера для конкретного пользователя"""
        if is_start_dialog or user_id not in cls._instances:
            cls._instances[user_id] = cls(user_id)
            conv_logger.info(f"Создан новый менеджер разговора для пользователя {user_id}")
        return cls._instances[user_id]

    def __init__(self, user_id: str):
        """Инициализация менеджера разговора для конкретного пользователя"""
        self.user_id = user_id
        self.stage = ConversationStage.SYMPTOMS
        self.pending_stage = None
        self.problem_info = ProblemInfo([])
        self.patient_info = PatientInfo()
        self.error_state = False
        conv_logger.info(
            f"Инициализирован новый менеджер разговора для пользователя {user_id}. Начальный этап: SYMPTOMS")

    def get_conversation_state(self) -> dict:
        """Возвращает текущее состояние диалога"""
        return {
            "symptoms": self.problem_info.symptoms.copy(),
            "patient_info": self.patient_info.to_dict(),
            "current_stage": self.stage.name if self.stage else None,
            "next_stage": self.pending_stage.name if self.pending_stage else None,
            "has_error": self.error_state
        }

    def process_message(self, message: str, messages: List[dict]) -> dict:
        """Обрабатывает сообщение пользователя, планирует переход этапа после ответа ассистента"""
        try:
            self.error_state = False
            old_stage = self.stage
            self.pending_stage = None  # Сбрасываем ожидающий этап

            if self.stage == ConversationStage.SYMPTOMS:
                # Извлекаем симптомы из всех сообщений, включая текущее
                temp_messages = messages + [{"role": "user", "content": message}]
                symptoms = ProblemInfo.extract_symptoms(temp_messages)
                if symptoms:
                    self.problem_info.symptoms.extend(symptoms)

                # Планируем переход на PATIENT_INFO после любого первого сообщения
                self.pending_stage = ConversationStage.PATIENT_INFO

            elif self.stage == ConversationStage.PATIENT_INFO:
                # Извлекаем информацию о пациенте
                age = self.patient_info.extract_age(message)
                if age is not None:
                    self.patient_info.age = age

                diseases = self.patient_info.extract_chronic_diseases(message)
                if diseases:
                    self.patient_info.chronic_diseases = diseases
                elif "нет хронических" in message.lower():
                    self.patient_info.chronic_diseases = []

                allergies = self.patient_info.extract_allergies(message)
                if allergies:
                    self.patient_info.allergies = allergies
                elif "нет аллергий" in message.lower():
                    self.patient_info.allergies = []

                # Планируем переход если вся информация собрана
                if self.patient_info.is_complete():
                    self.pending_stage = ConversationStage.DIAGNOSIS
                else:
                    self.pending_stage = ConversationStage.PATIENT_INFO

            # Логирование изменений
            conv_logger.info(f"Pending stage: {self.pending_stage}")
            
            return self.get_conversation_state()
            
        except Exception as e:
            conv_logger.error(f"Ошибка при обработке сообщения: {str(e)}")
            self.error_state = True
            return self.get_conversation_state()

    def apply_stage_transition(self):
        """Применяет запланированный переход этапа"""
        if self.pending_stage:
            conv_logger.info(f"Переход этапа с {self.stage.name} на {self.pending_stage.name}")
            self.stage = self.pending_stage
            self.pending_stage = None

    @classmethod
    def clear_user_session(cls, user_id: str):
        """Очищает сессию пользователя"""
        if user_id in cls._instances:
            del cls._instances[user_id]
            conv_logger.info(f"Сессия пользователя {user_id} очищена") 