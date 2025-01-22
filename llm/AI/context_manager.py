import logging
from typing import Dict
from langchain_community.vectorstores import FAISS
from medical_analyzer import MedicalContextAnalyzer, SearchResult
from text_preprocessing import clean_text
from logger_config import setup_logger

setup_logger()
logger = logging.getLogger('context_manager')

def get_relevant_context(query: str, vector_stores: Dict[str, FAISS], n_results: int = 5) -> str:
    """Получает релевантный контекст с использованием улучшенных методов поиска"""
    analyzer = MedicalContextAnalyzer()
    all_results = []
    
    logger.info(f"\n{'='*50}\nПоиск контекста для запроса: {query}\n{'='*50}")
    
    # Очищаем и подготавливаем запрос
    clean_query = clean_text(query)
    query_terms = analyzer.find_medical_terms(clean_query)
    logger.info(f"Найденные медицинские термины в запросе: {', '.join(query_terms)}")
    
    for category, store in vector_stores.items():
        try:
            # Получаем больше результатов для последующей фильтрации
            results = store.similarity_search_with_score(clean_query, k=n_results * 2)
            logger.info(f"\nПоиск в категории '{category}':")
            
            for doc, score in results:
                # Нормализуем score из FAISS (меньше = лучше) в релевантность (больше = лучше)
                base_relevance = 1 / (1 + score)  # Преобразуем в диапазон (0, 1]
                
                # Находим медицинские термины в тексте
                medical_terms = analyzer.find_medical_terms(doc.page_content)
                medical_relevance = analyzer.calculate_medical_relevance(
                    doc.page_content, clean_query
                )
                
                # Рассчитываем итоговый скор как взвешенную сумму
                final_score = (base_relevance * 0.7) + (medical_relevance * 0.3)
                
                result = SearchResult(
                    category=category,
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=final_score,
                    medical_terms=medical_terms
                )
                
                logger.info(
                    f"\nНайден релевантный фрагмент:"
                    f"\nБазовая релевантность: {base_relevance:.2%}"
                    f"\nМедицинская релевантность: {medical_relevance:.2%}"
                    f"\nИтоговая релевантность: {final_score:.2%}"
                    f"\nНайденные термины: {', '.join(medical_terms)}"
                )
                
                all_results.append(result)
                
        except Exception as e:
            logger.error(f"Ошибка при поиске в категории {category}: {e}")
            continue
    
    # Сортируем результаты по релевантности (больше = лучше)
    all_results.sort(key=lambda x: x.score, reverse=True)
    
    # Формируем итоговый контекст
    context = "\n\nРелевантная информация из медицинской литературы:\n"
    logger.info(f"\n{'='*50}\nИтоговый контекст:")
    
    for i, result in enumerate(all_results[:n_results], 1):
        medical_terms_str = ', '.join(result.medical_terms) if result.medical_terms else 'не найдены'
        
        chunk_text = (
            f"\nИз раздела {result.category}"
            f" (релевантность: {result.score:.1%}):\n"
            f"{result.content}\n"
            f"Источник: стр. {result.metadata.get('page', 'н/д')}\n"
            f"Медицинские термины: {medical_terms_str}\n"
            f"{'-'*40}"
        )
        context += chunk_text
        logger.info(f"\nЧанк {i} в итоговом контексте:{chunk_text}")
    
    logger.info(f"{'='*50}\n")
    return context 