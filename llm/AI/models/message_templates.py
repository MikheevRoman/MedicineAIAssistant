from dataclasses import dataclass
from typing import List

@dataclass
class StageMessages:
    messages: List[str]

# Сообщения для команд start и clear
START_MESSAGES = StageMessages([
    "Здравствуйте! Я - медицинский ассистент, который поможет вам разобраться с вашими симптомами. "
    "Я могу собрать информацию о вашем состоянии и предложить предварительный диагноз, "
    "а также подсказать, к какому специалисту лучше обратиться.",
    
    "Для начала мне нужно задать несколько вопросов о пациенте:\n"
        "- Сколько вам лет?\n"
        "- Есть ли у вас хронические заболевания?\n"
        "- Есть ли у вас аллергии на что-либо?"
])

# Сообщения для перехода между этапами
STAGE_TRANSITION_MESSAGES = {
    "PATIENT_INFO_TO_SYMPTOMS": StageMessages([
        "Спасибо что ответили на вопросы. Теперь перейдем к "
        "Пожалуйста, опишите ваши симптомы как можно подробнее. "
        "Например: как давно они появились, насколько они сильные, "
        "что может усиливать или ослаблять симптомы."
    ]),
    
    "SYMPTOMS_TO_DIAGNOSIS": StageMessages([
        "Спасибо за предоставленную информацию. На основе собранных данных я сейчас проанализирую вашу ситуацию "
        "и предложу предварительный диагноз, а также подскажу, к какому специалисту лучше обратиться."
    ])
}

# Сообщения для запроса недостающей информации
INCOMPLETE_INFO_MESSAGES = {
    "MISSING_AGE": "Пожалуйста, укажите ваш возраст.",
    "MISSING_CHRONIC_DISEASES": "Расскажите, есть ли у вас хронические заболевания? Если нет, так и напишите.",
    "MISSING_ALLERGIES": "Есть ли у вас какие-либо аллергии? Если нет, так и напишите."
} 