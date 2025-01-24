import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from logging_config import setup_logger

# Инициализация логгера
text_logger = setup_logger('text_preprocessing', 'FILE_OPERATIONS_LOGGING')

def clean_text(text: str) -> str:
    """Очищает текст от лишних пробелов и специальных символов"""
    text_logger.info("Начало очистки текста")
    original_length = len(text)
    
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
    text = text.strip()
    
    cleaned_length = len(text)
    text_logger.info(f"Очистка текста завершена. Размер уменьшен с {original_length} до {cleaned_length} символов")
    return text

def create_medical_text_splitter() -> RecursiveCharacterTextSplitter:
    """Создает оптимизированный разделитель текста для медицинских документов"""
    text_logger.info("Создание разделителя текста для медицинских документов")
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", ";", ":", " ", ""],
        chunk_size=4000,
        chunk_overlap=600,
        length_function=len,
        is_separator_regex=False
    )
    text_logger.info(f"Разделитель создан с размером чанка {4000} и перекрытием {600}")
    return splitter 