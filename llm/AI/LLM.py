import json
import requests
from dotenv import load_dotenv
from flask import Flask, request, Response, stream_with_context, jsonify
from openai import OpenAI
import os
from embeddings_handler import CustomEmbeddings
from pdf_processor import load_and_process_pdfs
from context_manager import get_relevant_context
from managers.conversation_manager import ConversationManager
from logging_config import setup_logger
from waitress import serve
from typing import List

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

# Инициализация компонентов, не зависящих от пользователя
embeddings = CustomEmbeddings()
vector_stores = load_and_process_pdfs()

@app.route('/check-uc', methods=['POST'])
def process_data():
    try:
        data = request.get_json()
        messages = data.get('prompt', [])
        user_id = data.get('user_id')
        is_start_dialog = data.get('is_start_dialog', False)
        
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
        
        last_user_message = next((msg['content'] for msg in reversed(messages) 
                                if msg['role'] == 'user'), '')
        
        # Получаем или создаем менеджер разговора для пользователя
        conversation_manager, start_messages = ConversationManager.get_instance(user_id, is_start_dialog)
        
        # Обработка сообщения и обновление состояния разговора
        conversation_state, additional_messages = conversation_manager.process_message(last_user_message, messages)
        
        if conversation_state.get('has_error', False):
            return Response(
                json.dumps({"error": "Error processing message"}),
                status=500,
                mimetype='application/json'
            )

        # Если это начало диалога, добавляем стартовые сообщения
        if is_start_dialog:
            conversation_state['messages'] = start_messages
        elif additional_messages:
            conversation_state['messages'] = additional_messages

        # Получение системного промпта для текущей стадии
        system_message = get_system_prompt(conversation_state)
        
        # Добавление контекста из RAG только на стадии диагностики
        if conversation_state['current_stage'] == 'DIAGNOSIS':
            rag_logger.info("Получение релевантного контекста из базы знаний")
            context = get_relevant_context(last_user_message, vector_stores)
            system_message["content"] += f"\n\nКонтекст из медицинской литературы:\n{context}"
            rag_logger.info("Контекст успешно получен")
        
        full_messages = [system_message] + messages
        
        # Применяем переход этапа после формирования промпта
        if conversation_state.get('next_stage'):
            conversation_manager.apply_stage_transition()

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
        # Генерируем полный ответ
        full_response = []
        current_conversation_state = {}  # Переименовали переменную для избежания конфликта

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

        return jsonify({
            "response": ''.join(full_response),
            "conversation_state": current_conversation_state
        })

    except Exception as e:
        api_logger.error(f"Ошибка в синхронном запросе: {str(e)}")
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
        
        # Формируем ответ
        response_data = {
            "messages": [
                "История диалога очищена." if is_clear_command else None,
                "Здравствуйте! Я медицинский ассистент, созданный для помощи в предварительной диагностике.",
                "Пожалуйста, опишите, что вас беспокоит."
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
        api_logger.error(f"Ошибка при получении приветственных сообщений: {str(e)}")
        return Response(
            json.dumps({"error": "Internal server error"}),
            status=500,
            mimetype='application/json'
        )

def get_system_prompt(conversation_state: dict) -> dict:
    """Возвращает системный промпт в зависимости от текущей стадии разговора"""
    current_stage = conversation_state['current_stage']
    
    if current_stage == 'SYMPTOMS':
        prompt_content = (
            "Вы - медицинский ассистент. Ваша задача - собрать информацию о симптомах пациента. "
            "Задавайте уточняющие вопросы о характере и длительности симптомов. "
            "На этом этапе НЕ нужно спрашивать про возраст и хронические заболевания."
        )
    elif current_stage == 'PATIENT_INFO':
        prompt_content = (
            "Вы - медицинский ассистент. Ваша задача - собрать информацию о пациенте: "
            "- возраст\n"
            "- наличие хронических заболеваний\n"
            "- наличие аллергий\n"
            "Задавайте только эти вопросы. НЕ переходите к диагностике."
        )
    else:  # DIAGNOSIS
        patient_info = conversation_state['patient_info']
        prompt_content = (
            "Вы - медицинский ассистент. На основе собранной информации:\n"
            f"Симптомы: {', '.join(conversation_state['symptoms'])}\n"
            f"Возраст: {patient_info['age']}\n"
            f"Хронические заболевания: {', '.join(patient_info['chronic_diseases']) if patient_info['chronic_diseases'] else 'нет'}\n"
            f"Аллергии: {', '.join(patient_info['allergies']) if patient_info['allergies'] else 'нет'}\n\n"
            "Предложите предварительный диагноз и укажите к какому специалисту обратиться. "
            "При наличии опасных симптомов рекомендуйте немедленно обратиться за медицинской помощью."
        )

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