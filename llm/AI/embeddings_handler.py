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
    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
                    emb_logger.info(f"Инициализация модели {self.model_name}")
                    self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                    self.model = AutoModel.from_pretrained(self.model_name)
                    self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                    self.model.to(self.device)
                    emb_logger.info(f"Модель загружена на устройство: {self.device}")
                    self._initialized = True

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Извлекает текст из PDF файла"""
        try:
            file_logger.info(f"Извлечение текста из PDF: {pdf_path}")
            document = fitz.open(pdf_path)
            text = ""
            for page_num in range(len(document)):
                page = document.load_page(page_num)
                text += page.get_text("text")
            file_logger.info(f"Успешно извлечен текст из {len(document)} страниц")
            return text
        except Exception as e:
            file_logger.error(f"Ошибка при извлечении текста из PDF {pdf_path}: {e}")
            return ""

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Генерирует эмбеддинги для списка текстов"""
        try:
            emb_logger.info(f"Генерация эмбеддингов для {len(texts)} текстов")
            self.model.eval()
            all_embeddings = []
            
            for i, text in enumerate(texts, 1):
                inputs = self.tokenizer(
                    text, 
                    return_tensors="pt", 
                    truncation=True, 
                    padding=True, 
                    max_length=512
                ).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                
                embeddings = outputs.last_hidden_state.mean(dim=1)
                embeddings = embeddings.cpu().numpy()[0].tolist()
                all_embeddings.append(embeddings)
                
                if i % 100 == 0:
                    emb_logger.info(f"Обработано {i}/{len(texts)} текстов")
            
            emb_logger.info("Генерация эмбеддингов завершена")
            return all_embeddings
        except Exception as e:
            emb_logger.error(f"Ошибка при генерации эмбеддингов: {e}")
            return []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Обязательный метод из интерфейса Embeddings"""
        emb_logger.info(f"Запрос на эмбеддинг {len(texts)} документов")
        return self.generate_embeddings(texts)

    def embed_query(self, text: str) -> List[float]:
        """Обязательный метод из интерфейса Embeddings"""
        emb_logger.info("Запрос на эмбеддинг одиночного текста")
        return self.generate_embeddings([text])[0] 