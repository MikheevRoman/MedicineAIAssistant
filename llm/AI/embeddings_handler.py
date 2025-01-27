import os
os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'

import fitz
from transformers import AutoTokenizer, AutoModel
import torch
from typing import List
from langchain.embeddings.base import Embeddings
from logging_config import setup_logger
import threading

# Инициализация логгеров
emb_logger = setup_logger('embeddings', 'EMBEDDINGS_LOGGING')
file_logger = setup_logger('embeddings_file', 'FILE_OPERATIONS_LOGGING')

class CustomEmbeddings(Embeddings):
    """
        Класс для создания и управления эмбеддингами. Реализует паттерн Singleton для загрузки модели.
    """
    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls):
        """Создание единственного экземпляра класса (Singleton)"""
        if cls._instance is None:
            with cls._lock: # Синхронизация потоков
                if cls._instance is None: # Повторная проверка внутри блокировки
                    cls._instance = super().__new__(cls) # Создание нового экземпляра
        return cls._instance

    def __init__(self):
        """Инициализация модели и токенизатора"""
        if not self._initialized: # Проверка, был ли уже инициализирован объект
            with self._lock:
                if not self._initialized:
                    # Название модели для эмбеддингов (модель легкая и спокойно работает на процессоре)
                    self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
                    emb_logger.info(f"Инициализация модели {self.model_name}")
                    self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)  # Загрузка токенизатора
                    self.model = AutoModel.from_pretrained(self.model_name) # Загрузка модели
                    self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu") # Определение устройства (GPU/CPU)
                    self.model.to(self.device) # Перенос модели на выбранное устройство
                    emb_logger.info(f"Модель загружена на устройство: {self.device}")
                    self._initialized = True # Установка флага инициализации

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Извлечение текста из PDF файла.

        Аргументы:
        - pdf_path: Путь к PDF файлу.

        Возвращает:
        - Извлеченный текст в виде строки.
        """
        try:
            file_logger.info(f"Извлечение текста из PDF: {pdf_path}")
            document = fitz.open(pdf_path) # Открытие PDF файла
            text = ""
            for page_num in range(len(document)): # Итерация по страницам PDF
                page = document.load_page(page_num) # Загрузка страницы
                text += page.get_text("text") # Извлечение текста со страницы
            file_logger.info(f"Успешно извлечен текст из {len(document)} страниц")
            return text
        except Exception as e:
            file_logger.error(f"Ошибка при извлечении текста из PDF {pdf_path}: {e}")
            return ""

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Генерация эмбеддингов для списка текстов.

        Аргументы:
        - texts: Список текстов для преобразования в эмбеддинги.

        Возвращает:
        - Список эмбеддингов в виде списков чисел.
        """
        try:
            emb_logger.info(f"Генерация эмбеддингов для {len(texts)} текстов")
            self.model.eval() # Установка модели в режим оценки
            all_embeddings = [] # Список для хранения эмбеддингов
            
            for i, text in enumerate(texts, 1):  # Итерация по текстам с индексацией
                inputs = self.tokenizer(
                    text, 
                    return_tensors="pt",  # Преобразование текста в формат тензоров
                    truncation=True,  # Обрезка длинных текстов
                    padding=True,   # Добавление паддинга
                    max_length=512 # Максимальная длина текста
                ).to(self.device) # Перенос данных на устройство (CPU/GPU)
                
                with torch.no_grad(): # Отключение градиентов для ускорения
                    outputs = self.model(**inputs) # Пропуск текста через модель
                
                embeddings = outputs.last_hidden_state.mean(dim=1) # Усреднение скрытых состояний
                embeddings = embeddings.cpu().numpy()[0].tolist() # Перевод тензора в список чисел
                all_embeddings.append(embeddings) # Добавление эмбеддинга в список
                
                if i % 100 == 0: # Логирование каждые 100 текстов
                    emb_logger.info(f"Обработано {i}/{len(texts)} текстов")
            
            emb_logger.info("Генерация эмбеддингов завершена")
            return all_embeddings
        except Exception as e:
            emb_logger.error(f"Ошибка при генерации эмбеддингов: {e}")
            return []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
                Обязательный метод из интерфейса Embeddings для обработки списка документов.

                Аргументы:
                - texts: Список текстов.

                Возвращает:
                - Эмбеддинги текстов.
                """
        """Обязательный метод из интерфейса Embeddings"""
        emb_logger.info(f"Запрос на эмбеддинг {len(texts)} документов")
        return self.generate_embeddings(texts)

    def embed_query(self, text: str) -> List[float]:
        """
        Обязательный метод из интерфейса Embeddings для обработки одиночного текста.

        Аргументы:
        - text: Одиночный текст.

        Возвращает:
        - Эмбеддинг текста.
        """
        emb_logger.info("Запрос на эмбеддинг одиночного текста")
        return self.generate_embeddings([text])[0] 