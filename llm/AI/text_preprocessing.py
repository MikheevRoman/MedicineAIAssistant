import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from logging_config import setup_logger

# Инициализация логгера
text_logger = setup_logger('text_preprocessing', 'FILE_OPERATIONS_LOGGING')

def clean_text(text: str) -> str:
    """Очищает текст от лишних пробелов и специальных символов.

    Args:
        text (str): Исходный текст для обработки

    Returns:
        str: Очищенный текст

    Логирует:
        - Старт и завершение процесса очистки
        - Размер текста до и после обработки
    """
    text_logger.info("Начало очистки текста")
    original_length = len(text)

    # Замена множественных пробелов на одинарные
    text = re.sub(r'\s+', ' ', text)

    # Удаление специальных символов, кроме базовой пунктуации и буквенно-цифровых
    text = re.sub(r'[^\w\s.,;:!?()-]', '', text)

    # Удаление пробелов в начале и конце текста
    text = text.strip()
    
    cleaned_length = len(text)
    text_logger.info(f"Очистка текста завершена. Размер уменьшен с {original_length} до {cleaned_length} символов")
    return text

def create_medical_text_splitter() -> RecursiveCharacterTextSplitter:
    """Создает оптимизированный разделитель текста для медицинских документов.

    Returns:
        RecursiveCharacterTextSplitter: Настроенный экземпляр разделителя

    Особенности:
        - Использует иерархию разделителей от абзацев до отдельных слов
        - Большой размер чанка (4000 символов) для сохранения контекста
        - Значительное перекрытие чанков (600 символов) для сохранения связности
    """
    text_logger.info("Создание разделителя текста для медицинских документов")

    # Инициализация разделителя с особыми параметрами для медицинских текстов
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", ";", ":", " ", ""], # Иерархия разделителей
        chunk_size=4000,     # Оптимально для длинных медицинских документов
        chunk_overlap=600,   # Большое перекрытие для сохранения контекста
        length_function=len, # Использование стандартной длины строки
        is_separator_regex=False
    )
    text_logger.info(f"Разделитель создан с размером чанка {4000} и перекрытием {600}")
    return splitter 