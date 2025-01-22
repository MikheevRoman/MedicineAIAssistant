import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging
from logger_config import setup_logger

setup_logger()
logger = logging.getLogger('text_preprocessing')

def clean_text(text: str) -> str:
    """Очищает текст от лишних пробелов и специальных символов"""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
    return text.strip()

def create_medical_text_splitter() -> RecursiveCharacterTextSplitter:
    """Создает оптимизированный разделитель текста для медицинских документов"""
    return RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", ";", ":", " ", ""],
        chunk_size=2000,
        chunk_overlap=300,
        length_function=len,
        is_separator_regex=False
    ) 