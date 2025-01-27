import os
import logging
from typing import Dict

# Флаги логирования (0 - выключено, 1 - включено)
LOG_FLAGS = {
    # Логирование RAG системы
    "RAG_LOGGING": int(os.getenv('RAG_LOGGING', '1')),
    
    # Логирование диалогов
    "CONVERSATION_LOGGING": int(os.getenv('CONVERSATION_LOGGING', '1')),
    
    # Логирование обработки PDF
    "PDF_PROCESSING_LOGGING": int(os.getenv('PDF_PROCESSING_LOGGING', '1')),
    
    # Логирование embeddings
    "EMBEDDINGS_LOGGING": int(os.getenv('EMBEDDINGS_LOGGING', '1')),
    
    # Логирование медицинского анализатора
    "MEDICAL_ANALYZER_LOGGING": int(os.getenv('MEDICAL_ANALYZER_LOGGING', '1')),
    
    # Логирование API запросов
    "API_LOGGING": int(os.getenv('API_LOGGING', '1')),
    
    # Логирование работы с файлами
    "FILE_OPERATIONS_LOGGING": int(os.getenv('FILE_OPERATIONS_LOGGING', '1')),
    
    # Логирование ошибок (всегда включено)
    "ERROR_LOGGING": 1
}

class LogFilter:
    def __init__(self, log_type: str):
        self.log_type = log_type
    
    def filter(self, record):
        if record.levelno == logging.ERROR and LOG_FLAGS["ERROR_LOGGING"]:
            return True
        return LOG_FLAGS.get(self.log_type, 0)

def setup_logger(name: str, log_type: str) -> logging.Logger:
    """
    Настраивает логгер с определенным типом логирования
    
    Args:
        name: Имя логгера
        log_type: Тип логирования из LOG_FLAGS
    """

    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Создаем форматтер с информацией о модуле
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(log_type)s] - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Добавляем фильтр для контроля логирования
        log_filter = LogFilter(log_type)
        
        # Настраиваем вывод в файл
        file_handler = logging.FileHandler(f'logs/{name}.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.addFilter(log_filter)
        
        # Настраиваем вывод в консоль
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.addFilter(log_filter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Добавляем дополнительную информацию о типе логирования
        logger = logging.LoggerAdapter(logger, {'log_type': log_type})
    
    return logger 