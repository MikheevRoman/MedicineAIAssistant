from dataclasses import dataclass
from typing import List, Dict, Any
import json
import logging
from llm.logger_config import setup_logger

setup_logger()
logger = logging.getLogger('medical_analyzer')

@dataclass
class SearchResult:
    """Структура для хранения результата поиска"""
    category: str
    content: str
    metadata: Dict[str, Any]
    score: float
    medical_terms: List[str] = None
    symptom_match: bool = False
    diagnostic_match: bool = False
    treatment_match: bool = False

class MedicalContextAnalyzer:
    """Анализатор медицинского контекста"""
    
    def __init__(self):
        """Инициализация анализатора и загрузка медицинских терминов"""
        self.medical_terms = self._load_medical_terms()
    
    @staticmethod
    def _load_medical_terms() -> Dict[str, List[str]]:
        """Загружает медицинские термины из JSON файла"""
        try:
            with open('../medical_terms.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка при загрузке medical_terms.json: {e}")
            return {}
    
    def find_medical_terms(self, text: str) -> List[str]:
        """Находит медицинские термины в тексте"""
        found_terms = []
        text_lower = text.lower()
        
        for category, terms in self.medical_terms.items():
            for term in terms:
                if term in text_lower:
                    found_terms.append(term)
        
        return found_terms

    def calculate_medical_relevance(self, text: str, query: str) -> float:
        """Рассчитывает медицинскую релевантность текста"""
        text_terms = set(self.find_medical_terms(text))
        query_terms = set(self.find_medical_terms(query))
        
        if not text_terms:
            return 0.0
            
        term_overlap = len(text_terms.intersection(query_terms))
        term_score = term_overlap / len(text_terms) if text_terms else 0
        
        return term_score