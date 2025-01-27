from typing import List, Tuple
from logging_config import setup_logger
from AI.models.conversation_stage import ConversationStage
from AI.models.problem_info import ProblemInfo
from AI.models.patient_info import PatientInfo
from AI.models.message_templates import START_MESSAGES, STAGE_TRANSITION_MESSAGES, INCOMPLETE_INFO_MESSAGES

# Инициализация логгеров
conv_logger = setup_logger('conversation', 'CONVERSATION_LOGGING')
api_logger = setup_logger('conversation_api', 'API_LOGGING')

class ConversationManager:
    _instances = {}  # Словарь для хранения экземпляров менеджера для каждого пользователя

    @classmethod
    def get_instance(cls, user_id: str, is_start_dialog: bool = False) -> Tuple['ConversationManager', List[str]]:
        """Получает или создает экземпляр менеджера для конкретного пользователя"""
        messages_to_send = []
        
        if is_start_dialog or user_id not in cls._instances:
            cls._instances[user_id] = cls(user_id)
            conv_logger.info(f"Создан новый менеджер разговора для пользователя {user_id}")
            # Добавляем стартовые сообщения
            messages_to_send.extend(START_MESSAGES.messages)
            
        return cls._instances[user_id], messages_to_send

    def __init__(self, user_id: str):
        """Инициализация менеджера разговора для конкретного пользователя"""
        self.user_id = user_id
        self.stage = ConversationStage.PATIENT_INFO
        self.pending_stage = None
        self.problem_info = ProblemInfo([])
        self.patient_info = PatientInfo()
        self.error_state = False
        conv_logger.info(
            f"Инициализирован новый менеджер разговора для пользователя {user_id}. Начальный этап: SYMPTOMS")


    def set_stage(self, stage: ConversationStage):
        """Устанавливает текущий этап разговора"""
        self.stage = stage
        conv_logger.info(f"Этап разговора для пользователя {self.user_id} установлен на {stage.name}")


    def get_conversation_state(self) -> dict:
        """Возвращает текущее состояние диалога"""
        return {
            "symptoms": self.problem_info.symptoms.copy(),
            "patient_info": self.patient_info.to_dict(),
            "current_stage": self.stage.name if self.stage else None,
            "next_stage": self.pending_stage.name if self.pending_stage else None,
            "has_error": self.error_state
        }

    def process_message(self, message: str, messages: List[dict]) -> Tuple[dict, List[str]]:
        """Обрабатывает сообщение пользователя, планирует переход этапа после ответа ассистента"""
        try:
            self.error_state = False
            old_stage = self.stage
            self.pending_stage = None  # Сбрасываем ожидающий этап
            messages_to_send = []

            if self.stage == ConversationStage.SYMPTOMS:
                temp_messages = messages + [{"role": "user", "content": message}]
                self.problem_info.extract_symptoms(temp_messages)

                if self.problem_info.symptoms_complete:
                    self.pending_stage = ConversationStage.DIAGNOSIS
                    if old_stage != self.pending_stage:
                        # Добавляем сообщение о переходе и очищаем другие сообщения
                        messages_to_send = STAGE_TRANSITION_MESSAGES["SYMPTOMS_TO_DIAGNOSIS"].messages.copy()

            elif self.stage == ConversationStage.PATIENT_INFO:
                prev_message = next((msg['content'] for msg in reversed(messages) if msg['role'] == 'assistant'), None)
                age = self.patient_info.extract_age(message, prev_message)
                diseases = self.patient_info.extract_chronic_diseases(message, prev_message)
                allergies = self.patient_info.extract_allergies(message, prev_message)

                conv_logger.info(
                    f"Собранная информация о пациенте:\n"
                    f"Возраст: {self.patient_info.age}\n"
                    f"Хронические заболевания: {self.patient_info.chronic_diseases if self.patient_info.has_chronic_diseases else 'нет'}\n"
                    f"Аллергии: {self.patient_info.allergies if self.patient_info.has_allergies else 'нет'}"
                )

                # Проверяем, какой информации не хватает
                missing_info = []
                if self.patient_info.age is None:
                    missing_info.append(INCOMPLETE_INFO_MESSAGES["MISSING_AGE"])
                elif self.patient_info.has_chronic_diseases and not self.patient_info.chronic_diseases:
                    missing_info.append(INCOMPLETE_INFO_MESSAGES["MISSING_CHRONIC_DISEASES"])
                elif self.patient_info.has_allergies and not self.patient_info.allergies:
                    missing_info.append(INCOMPLETE_INFO_MESSAGES["MISSING_ALLERGIES"])

                if missing_info:
                    messages_to_send.extend(missing_info)
                    self.pending_stage = ConversationStage.PATIENT_INFO
                else:
                    self.pending_stage = ConversationStage.SYMPTOMS
                    if old_stage != self.pending_stage:
                        messages_to_send = STAGE_TRANSITION_MESSAGES["PATIENT_INFO_TO_SYMPTOMS"].messages.copy()

            elif self.stage == ConversationStage.DIAGNOSIS:
                self.pending_stage = ConversationStage.DIAGNOSIS

            # Определяем, произошел ли переход этапа
            transition_occurred = old_stage != self.pending_stage

            # Если переход произошел, оставляем только сообщения о переходе
            if transition_occurred and messages_to_send:
                # Фильтруем сообщения, оставляем только переходные
                transition_messages = []
                for msg in messages_to_send:
                    if any(msg in transition_msgs.messages for transition_msgs in STAGE_TRANSITION_MESSAGES.values()):
                        transition_messages.append(msg)
                messages_to_send = transition_messages

            conv_logger.info(
                f"Текущий этап: {self.stage.name}, Следующий этап: {self.pending_stage.name if self.pending_stage else 'None'}")

            return self.get_conversation_state(), messages_to_send

        except Exception as e:
            conv_logger.error(f"Ошибка при обработке сообщения: {str(e)}")
            self.error_state = True
            return self.get_conversation_state(), []

    def apply_stage_transition(self):
        """Применяет запланированный переход этапа"""
        if self.pending_stage:
            conv_logger.info(f"Переход этапа с {self.stage.name} на {self.pending_stage.name}")
            self.stage = self.pending_stage
            self.pending_stage = None

    @classmethod
    def clear_user_session(cls, user_id: str) -> List[str]:
        """Очищает сессию пользователя"""
        if user_id in cls._instances:
            del cls._instances[user_id]
            conv_logger.info(f"Сессия пользователя {user_id} очищена")
            return START_MESSAGES.messages
        return [] 