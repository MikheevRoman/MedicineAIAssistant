import os
os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'

import fitz
from transformers import AutoTokenizer, AutoModel
import torch
from typing import List
import logging
from langchain.embeddings.base import Embeddings
from logger_config import setup_logger
import threading

setup_logger()
logger = logging.getLogger('embeddings_handler')

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
                    logger.info(f"Инициализация модели {self.model_name}")
                    self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                    self.model = AutoModel.from_pretrained(self.model_name)
                    self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                    self.model.to(self.device)
                    logger.info(f"Модель загружена на устройство: {self.device}")
                    self._initialized = True

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Извлекает текст из PDF файла"""
        try:
            document = fitz.open(pdf_path)
            text = ""
            for page_num in range(len(document)):
                page = document.load_page(page_num)
                text += page.get_text("text")
            return text
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста из PDF {pdf_path}: {e}")
            return ""

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Генерирует эмбеддинги для списка текстов"""
        try:
            self.model.eval()
            all_embeddings = []
            
            for text in texts:
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
            
            return all_embeddings
        except Exception as e:
            logger.error(f"Ошибка при генерации эмбеддингов: {e}")
            return []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Обязательный метод из интерфейса Embeddings"""
        return self.generate_embeddings(texts)

    def embed_query(self, text: str) -> List[float]:
        """Обязательный метод из интерфейса Embeddings"""
        return self.generate_embeddings([text])[0] 