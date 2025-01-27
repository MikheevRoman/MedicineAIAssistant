import base64
import json
import tempfile
import re
import requests
from dotenv import load_dotenv
from flask import Flask, request, Response, stream_with_context, jsonify, current_app
from openai import OpenAI
import os

from AI.image_process import generate_from_image
from AI.models import ConversationStage
from embeddings_handler import CustomEmbeddings
from pdf_processor import load_and_process_pdfs
from context_manager import get_relevant_context
from managers.conversation_manager import ConversationManager
from logging_config import setup_logger
from waitress import serve
from typing import List
from models.message_templates import START_MESSAGES

# Инициализация логгеров для разных компонентов
api_logger = setup_logger('api', 'API_LOGGING')
rag_logger = setup_logger('rag', 'RAG_LOGGING')

load_dotenv()

# Проверка режима работы сервера
PRODUCTION_MODE = bool(int(os.getenv('PRODUCTION_SERVER', '0')))

app = Flask(__name__)

PROXY_API_KEY = os.getenv('PROXY_API_KEY')
PROXY_OPENAI_URL = "https://api.proxyapi.ru/openai/v1/chat/completions"

OPENAI_HEADERS = {
    "Authorization": f"Bearer {PROXY_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "text/event-stream"
}

client = OpenAI(
    api_key=f"{os.getenv('PROXY_API_KEY')}",
    base_url="https://api.proxyapi.ru/openai/v1/chat/completions",
)

# Загрузка векторных данных и обработка PDF
embeddings = CustomEmbeddings()
vector_stores = load_and_process_pdfs()

@app.route('/check-uc', methods=['POST'])
def process_data():
    """
    Обработка асинхронного запроса от клиента.
    Основной маршрут для обработки пользовательских сообщений.
    """
    try:
        data = request.get_json()
        messages = data.get('prompt', [])
        user_id = data.get('user_id')
        is_start_dialog = data.get('is_start_dialog', False)

        # Проверка обязательных параметров
        if not user_id:
            api_logger.error("Отсутствует user_id в запросе")
            return Response(
                json.dumps({"error": "Missing user_id"}),
                status=400,
                mimetype='application/json'
            )

        api_logger.info(f"Получен новый запрос от пользователя {user_id}")
        api_logger.info(f"Начало нового диалога: {is_start_dialog}")
        api_logger.info(f"Количество сообщений: {len(messages)}")

        # Логика обработки сообщений
        last_user_message = next((msg['content'] for msg in reversed(messages)
                                if msg['role'] == 'user'), '')

        # Получение менеджера разговора и стартовых сообщений
        conversation_manager, start_messages = ConversationManager.get_instance(user_id, is_start_dialog)

        # Обработка сообщения через менеджер
        conversation_state, additional_messages = conversation_manager.process_message(last_user_message, messages)

        if conversation_state.get('has_error', False):
            return Response(
                json.dumps({"error": "Error processing message"}),
                status=500,
                mimetype='application/json'
            )

        # Добавление стартовых сообщений в случае начала диалога
        if is_start_dialog:
            conversation_state['messages'] = start_messages
        elif additional_messages:
            conversation_state['messages'] = additional_messages

        # Формирование системного промпта в зависимости от этапа диалога
        system_message = get_system_prompt(conversation_state)

        # Добавление релевантного контекста на этапе диагностики
        if conversation_state['current_stage'] == 'DIAGNOSIS':
            rag_logger.info("Получение релевантного контекста из базы знаний")
            context = get_relevant_context(last_user_message, vector_stores)
            system_message["content"] += f"\n\nКонтекст из медицинской литературы:\n{context}"
            rag_logger.info("Контекст успешно получен")

        # Полное сообщение для генерации ответа
        full_messages = [system_message] + messages

        # Обработка перехода на следующий этап
        if conversation_state.get('next_stage'):
            conversation_manager.apply_stage_transition()

        # Генерация ответа
        return Response(stream_with_context(generate(full_messages, conversation_state)),
                       mimetype='text/event-stream')

    except Exception as e:
        api_logger.error(f"Ошибка при обработке запроса: {str(e)}")
        return Response(
            json.dumps({"error": "Internal server error"}),
            status=500,
            mimetype='application/json'
        )


@app.route('/check-uc-sync', methods=['POST'])
def process_data_sync():
    """
        Обрабатывает синхронные POST-запросы от клиента для обработки текстовых сообщений.

        Логика:
        1. Принимает JSON с сообщениями от клиента.
        2. Выделяет последнее пользовательское сообщение.
        3. Создает или получает менеджер разговора для пользователя.
        4. Обрабатывает сообщение и текущий этап разговора.
        5. Генерирует ответ с учетом контекста и текущей стадии диалога.
        """
    try:
        data = request.get_json()
        messages = data.get('prompt', [])
        user_id = data.get('user_id')
        is_start_dialog = data.get('is_start_dialog', False)

        if not user_id:
            api_logger.error("Отсутствует user_id в запросе")
            return jsonify({"error": "Missing user_id"}), 400

        api_logger.info(f"Получен синхронный запрос от пользователя {user_id}")
        api_logger.info(f"Начало нового диалога: {is_start_dialog}")
        api_logger.info(f"Количество сообщений: {len(messages)}")

        last_user_message = next((msg['content'] for msg in reversed(messages)
                                  if msg['role'] == 'user'), '')

        # Получаем или создаем менеджер разговора
        conversation_manager, start_messages = ConversationManager.get_instance(user_id, is_start_dialog)

        # Обработка сообщения
        conversation_state, additional_messages = conversation_manager.process_message(last_user_message, messages)

        if conversation_state.get('has_error', False):
            return jsonify({"error": "Error processing message"}), 500

        # Добавляем стартовые сообщения если нужно
        if is_start_dialog:
            conversation_state['messages'] = start_messages
        elif additional_messages:
            conversation_state['messages'] = additional_messages

        # Формируем системный промпт
        system_message = get_system_prompt(conversation_state)

        # Добавляем RAG контекст для диагностики
        if conversation_state['current_stage'] == 'DIAGNOSIS':
            rag_logger.info("Получение контекста для синхронного запроса")
            context = get_relevant_context(last_user_message, vector_stores)
            system_message["content"] += f"\n\nКонтекст из медицинской литературы:\n{context}"

        full_messages = [system_message] + messages

        # Применяем переход этапа
        if conversation_state.get('next_stage'):
            conversation_manager.apply_stage_transition()

        # Генерируем полный ответ
        full_response = []
        current_conversation_state = {}
        is_twice = False
        if conversation_state.get('next_stage') == "Diagnosis":
            is_twice = True
            conversation_manager.set_stage(ConversationStage.DIAGNOSIS)

        for chunk in generate(full_messages, conversation_state):
            try:
                if chunk.startswith('data: '):
                    json_str = chunk[6:]  # Убираем префикс 'data: '
                    data = json.loads(json_str)

                    # Обрабатываем состояние диалога
                    if 'conversation_state' in data:
                        current_conversation_state = data['conversation_state']

                    # Обрабатываем контент сообщения
                    if 'choices' in data and len(data['choices']) > 0:
                        delta = data['choices'][0].get('delta', {})
                        if 'content' in delta:
                            full_response.append(delta['content'])

            except json.JSONDecodeError:
                continue
            except KeyError as e:
                api_logger.warning(f"Отсутствует ключ в чанке: {str(e)}")
            except IndexError as e:
                api_logger.warning(f"Пустой список choices в чанке: {str(e)}")
        if conversation_state.get('next_stage') and not is_twice:
            full_response = additional_messages
        print(full_response)
        return jsonify({
            "response": ''.join(full_response),
            "conversation_state": current_conversation_state
        })

    except Exception as e:
        api_logger.error(f"Ошибка в синхронном запросе: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/check-uc-sync-image', methods=['POST'])
def process_image_sync():
    """
    Обработчик маршрута для проверки синхронизации изображений.
    Метод принимает POST-запросы, выполняет обработку изображения,
    проверяет синхронизацию и возвращает соответствующий результат.
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        image_base64 = data.get('image')
        messages = data.get('prompt', [])
        is_start_dialog = data.get('is_start_dialog', False)

        if not user_id:
            api_logger.error("Отсутствует user_id в запросе с изображением")
            return jsonify({"error": "Missing user_id"}), 400

        if not image_base64:
            api_logger.error("Отсутствует изображение в запросе")
            return jsonify({"error": "Missing image"}), 400

        # Декодирование и сохранение изображения
        try:
            image_data = base64.b64decode(image_base64.split(',')[-1])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(image_data)
                image_path = temp_file.name
        except Exception as e:
            api_logger.error(f"Ошибка декодирования изображения: {str(e)}")
            return jsonify({"error": "Invalid image format"}), 400

        # Обработка изображения нейросетью
        try:
            image_response = ''.join(generate_from_image(image_path))
            print("Ответ от модели анализа изображений:", image_response)

            # Парсинг ответа нейросети
            symptoms_list = []
            match = re.search(r'\[(.*?)\]', image_response)
            if match:
                symptoms_str = match.group(1)
                symptoms_list = [s.strip() for s in symptoms_str.split(',') if s.strip()]

            # Обновление информации о проблеме в менеджере
            if symptoms_list:
                conversation_manager, _ = ConversationManager.get_instance(user_id, is_start_dialog)
                existing_symptoms = set(conversation_manager.problem_info.symptoms)

                new_symptoms = [symptom for symptom in symptoms_list if symptom not in existing_symptoms]
                conversation_manager.problem_info.symptoms.extend(new_symptoms)

                api_logger.info(f"Добавлены симптомы из изображения: {new_symptoms}")

        except Exception as e:
            api_logger.error(f"Ошибка при обработке изображения: {str(e)}")
            return jsonify({"error": "Image processing failed"}), 500
        finally:
            os.unlink(image_path)

        # Добавляем результат анализа в историю сообщений
        if symptoms_list:
            messages.append({
                "role": "system",
                "content": f"Анализ изображения выявил следующие проблемы: {', '.join(symptoms_list)}"
            })

        # Вызов основной логики обработки
        with current_app.test_request_context(
                '/check-uc-sync',
                method='POST',
                json={
                    'user_id': user_id,
                    'prompt': messages,
                    'is_start_dialog': False  # Используем существующий менеджер
                }
        ):
            response = process_data_sync()
            return response.get_json(), response.status_code

    except Exception as e:
        api_logger.error(f"Ошибка в обработке изображения: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/get-welcome-messages', methods=['POST'])
def get_welcome_messages():
    """Возвращает приветственные сообщения для команд start и clear"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        is_clear_command = data.get('is_clear_command', False)

        if not user_id:
            api_logger.error("Отсутствует user_id в запросе")
            return Response(
                json.dumps({"error": "Missing user_id"}),
                status=400,
                mimetype='application/json'
            )

        # Получаем менеджер разговора для пользователя
        conversation_manager, start_messages = ConversationManager.get_instance(user_id, True)

        # Формируем ответ, используя сообщения из message templates
        response_data = {
            "messages": [
                "История диалога очищена." if is_clear_command else None,
                *START_MESSAGES.messages  # Используем сообщения из START_MESSAGES
            ],
            "conversation_state": conversation_manager.get_conversation_state()
        }

        # Убираем None из списка сообщений
        response_data["messages"] = [msg for msg in response_data["messages"] if msg is not None]

        return Response(
            json.dumps(response_data),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        api_logger.error(f"Ошибка в get_welcome_messages: {str(e)}")
        return Response(
            json.dumps({"error": "Internal server error"}),
            status=500,
            mimetype='application/json'
        )

def get_system_prompt(conversation_state: dict) -> dict:
    """Возвращает системный промпт в зависимости от текущей стадии разговора"""
    current_stage = conversation_state['current_stage']
    
    if current_stage == 'SYMPTOMS':
        prompt_content = """Вы - медицинский ассистент. Ваша задача - детально собрать информацию о симптомах. Правила:
        1. Задавайте по одному уточняющему вопросу за раз
        2. Фокусируйтесь на:
           - Локализации симптома (где именно проявляется)
           - Характере (ноющая/острая боль, тип кашля и т.д.)
           - Длительности (когда началось, постоянное/периодическое)
           - Сопутствующих проявлениях (температура, тошнота)
        3. Избегайте медицинского жаргона
        4. Не упоминайте возраст, аллергии или хронические болезни

        Примеры вопросов:
        - "Опишите характер боли: она постоянная или приступообразная?"
        - "Сопровождается ли кашель выделением мокроты?"
        - "Замечали ли усиление симптомов в определенное время суток?"
        - "Можете оценить интенсивность боли по шкале от 1 до 10?"

        Особые случаи:
        - При опасных симптомах (кровотечения, потеря сознания): 
          "Рекомендую немедленно обратиться в скорую помощь! Повторите свой симптом для подтверждения"
        - Если симптомы неясны: "Попробуйте сравнить ощущение с чем-либо (например, 'как будто камень в груди')"
        """
    elif current_stage == 'PATIENT_INFO':
        prompt_content = """Вы - медицинский регистратор. Соберите строго:
        1. Возраст (только число, без дат)
        2. Хронические заболевания (текущие, не историю болезней)
        3. Аллергии (лекарственные/пищевые)

        Правила взаимодействия:
        - Задавайте вопросы ПО ОЧЕРЕДИ в указанном порядке
        - При получении ответа подтвердите его прежде чем перейти к следующему пункту
        - При неопределенных ответах уточняйте

        Структура диалога:
        1. Возраст: 
           - Если число 0-120: подтвердить и перейти дальше
           - Если не указан: "Уточните, пожалуйста, ваш возраст полных лет"

        2. Хронические заболевания:
           - При отрицании: "Подтверждаю, хронических заболеваний нет"
           - При наличии: "Перечислите через запятую официальные диагнозы"

        3. Аллергии:
           - При отрицании: "Подтверждаю, аллергий нет"
           - При наличии: "Уточните аллергены и тип реакции (например, 'пенициллин: отек')"

        Примеры:
        Пользователь: "Мне 30, аллергия на амброзию"
        Ответ: 
        "Возраст: 30 лет. 
        Хронические заболевания имеются? 
        (Если ответ 'нет':) Аллергия на амброзию зафиксирована. Спасибо!"
        """
    elif current_stage == 'DIAGNOSIS':
        patient_info = conversation_state['patient_info']
        prompt_content = f"""Вы - диагностический ассистент. Анализируйте ТОЛЬКО предоставленные данные:

        {patient_info}

        Структурируйте ответ:
        1. **Возможные диагнозы** (максимум 3, по приоритету):
           - [Название] (вероятность: низкая/средняя/высокая)
           - Обоснование: связь с симптомами + демография

        2. **Рекомендации**:
           - Специалист: [тип врача] + срок визита
           - Экстренные случаи: [красные флаги]
           - Самоконтроль: [симптомы для наблюдения]
           - **Запись к врачу**: 
             "Для немедленной записи к [специалисту] используйте кнопку 🖱️ *ЗАПИСАТЬСЯ* в левом нижнем углу экрана"

        3. **Ограничения**:
           - "Это предварительная оценка. Точный диагноз требует очного осмотра"
           - "При ухудшении состояния немедленно обратитесь в скорую помощь"

        Пример вывода:
        **2. Рекомендации:**
        - Консультация гастроэнтерологом в течение 7 дней
        - Опасные симптомы: рвота с кровью, черный стул
        - Мониторинг частоты симптомов
        - Для записи к гастроэнтерологу нажмите кнопку *"Записаться"* слева внизу ↘️
        """
    return {"role": "system", "content": prompt_content}

def generate(full_messages: List[dict], conversation_state: dict):
    payload = {
        "model": "gpt-4o-mini",
        "messages": full_messages,
        "max_tokens": 5000,
        "temperature": 0.7,
        "stream": True,
    }

    api_logger.info("Отправка запроса к OpenAI API")
    try:
        response = requests.post(
            PROXY_OPENAI_URL,
            headers=OPENAI_HEADERS,
            json=payload,
            stream=True
        )

        if response.status_code != 200:
            api_logger.error(f"Ошибка API OpenAI: {response.status_code}")
            error_response = {
                "error": "OpenAI API Error",
                "conversation_state": conversation_state
            }
            yield f"data: {json.dumps(error_response)}\n\n"
            return

        # Отправляем информацию о состоянии диалога в первом чанке
        initial_response = {
            "conversation_state": conversation_state
        }
        yield f"data: {json.dumps(initial_response)}\n\n"

        for line in response.iter_lines():
            if not line:
                continue
            
            try:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    if decoded_line.strip() == "data: [DONE]":
                        api_logger.info("Генерация ответа завершена")
                        break
                    yield f"{decoded_line}\n"
            except Exception as e:
                api_logger.error(f"Ошибка при обработке строки: {e}")
                continue

    except Exception as e:
        api_logger.error(f"Ошибка при выполнении запроса: {str(e)}")
        error_response = {
            "error": "Internal Server Error",
            "conversation_state": conversation_state
        }
        yield f"data: {json.dumps(error_response)}\n\n"

if __name__ == '__main__':
    if PRODUCTION_MODE:
        api_logger.info("Запуск сервера в production режиме (waitress)")
        serve(app, host='0.0.0.0', port=5000)
    else:
        api_logger.info("Запуск сервера в development режиме (Flask)")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # Отключаем автоперезагрузку
        )