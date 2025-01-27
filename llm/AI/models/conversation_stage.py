from enum import Enum


class ConversationStage(Enum):
    """
    Перечисление этапов диалога с пациентом.

    Этапы:
    PATIENT_INFO - Сбор общей информации о пациенте (возраст, хронические заболевания, аллергии)
    SYMPTOMS - Сбор информации о текущих симптомах
    DIAGNOSIS - Этап постановки предварительного диагноза
    """
    PATIENT_INFO = 1
    SYMPTOMS = 2
    DIAGNOSIS = 3