from dataclasses import dataclass
from typing import List, Dict, Any
import json
from logging_config import setup_logger

# Инициализация логгеров
med_logger = setup_logger('medical_analyzer', 'MEDICAL_ANALYZER_LOGGING')
file_logger = setup_logger('medical_analyzer_file', 'FILE_OPERATIONS_LOGGING')

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
        med_logger.info("Инициализация медицинского анализатора")
        self.medical_terms = self._load_medical_terms()
    
    @staticmethod
    def _load_medical_terms() -> Dict[str, List[str]]:
        """Загружает медицинские термины из JSON файла"""
        try:
            file_logger.info("Загрузка медицинских терминов из файла")
            with open('../medical_terms.json', 'r', encoding='utf-8') as f:
                terms = json.load(f)
            file_logger.info(f"Загружено {sum(len(v) for v in terms.values())} терминов из {len(terms)} категорий")
            return terms
        except Exception as e:
            file_logger.error(f"Ошибка при загрузке medical_terms.json: {e}")
            return {}
    
    def find_medical_terms(self, text: str) -> List[str]:
        """Находит медицинские термины в тексте"""
        found_terms = []
        text_lower = text.lower()
        
        med_logger.info("Поиск медицинских терминов в тексте")
        for category, terms in self.medical_terms.items():
            category_terms = []
            for term in terms:
                if term in text_lower:
                    category_terms.append(term)
            if category_terms:
                med_logger.info(f"Найдены термины в категории {category}: {', '.join(category_terms)}")
                found_terms.extend(category_terms)
        
        if found_terms:
            med_logger.info(f"Всего найдено терминов: {len(found_terms)}")
        else:
            med_logger.info("Медицинские термины не найдены")
        return found_terms

    def calculate_medical_relevance(self, text: str, query: str) -> float:
        """Рассчитывает медицинскую релевантность текста"""
        text_terms = set(self.find_medical_terms(text))
        query_terms = set(self.find_medical_terms(query))
        
        if not text_terms:
            med_logger.info("Текст не содержит медицинских терминов")
            return 0.0
            
        term_overlap = len(text_terms.intersection(query_terms))
        term_score = term_overlap / len(text_terms) if text_terms else 0
        
        med_logger.info(f"Релевантность текста: {term_score:.2%} "
                       f"(совпадение {term_overlap} из {len(text_terms)} терминов)")
        return term_score