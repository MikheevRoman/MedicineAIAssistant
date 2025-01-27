from typing import Dict
from langchain_community.vectorstores import FAISS
from medical_analyzer import MedicalContextAnalyzer, SearchResult
from text_preprocessing import clean_text
from logging_config import setup_logger

# Инициализация логгеров
rag_logger = setup_logger('context_manager', 'RAG_LOGGING')
file_logger = setup_logger('context_manager_file', 'FILE_OPERATIONS_LOGGING')

def get_relevant_context(query: str, vector_stores: Dict[str, FAISS], n_results: int = 5) -> str:
    """
    Получает релевантный контекст из векторных хранилищ.

    Аргументы:
    - query: Запрос пользователя.
    - vector_stores: Словарь векторных хранилищ, где ключ — категория, значение — объект FAISS.
    - n_results: Количество релевантных результатов для возврата.

    Возвращает:
    - Итоговый текст релевантного контекста.
    """
    analyzer = MedicalContextAnalyzer() # Инициализация анализатора медицинского контекста
    all_results = [] # Список всех найденных результатов
    
    rag_logger.info(f"\n{'='*50}\nПоиск контекста для запроса: {query}")
    rag_logger.info(f"Количество запрашиваемых результатов: {n_results}")
    rag_logger.info(f"Доступные категории: {', '.join(vector_stores.keys())}")
    
    # Очистка и предобработка запроса
    clean_query = clean_text(query)  # Удаление лишних символов и приведение к стандартному виду
    query_terms = analyzer.find_medical_terms(clean_query) # Извлечение медицинских терминов из запроса
    rag_logger.info(f"Очищенный запрос: {clean_query}")
    rag_logger.info(f"Найденные медицинские термины: {', '.join(query_terms)}")

    # Поиск контекста в каждой категории
    for category, store in vector_stores.items():
        try:
            rag_logger.info(f"\nПоиск в категории '{category}':")
            # Получение кандидатов результатов (с запасом для фильтрации)
            results = store.similarity_search_with_score(clean_query, k=n_results * 2)
            rag_logger.info(f"Получено {len(results)} результатов")

            # Обработка каждого результата
            for doc, score in results:
                # Нормализуем score из FAISS (меньше = лучше) в релевантность (больше = лучше)
                base_relevance = 1 / (1 + score)  # Преобразование значения из диапазона (0, ∞) в (0, 1]
                
                # Извлечение медицинских терминов из текста документа
                medical_terms = analyzer.find_medical_terms(doc.page_content)
                medical_relevance = analyzer.calculate_medical_relevance(
                    doc.page_content, clean_query # Оценка релевантности текста запросу
                )
                
                # Итоговая оценка релевантности как взвешенная сумма
                final_score = (base_relevance * 0.7) + (medical_relevance * 0.3)

                # Создание объекта результата
                result = SearchResult(
                    category=category,
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=final_score,
                    medical_terms=medical_terms
                )
                
                rag_logger.info(
                    f"\nНайден релевантный фрагмент:"
                    f"\nБазовая релевантность: {base_relevance:.2%}"
                    f"\nМедицинская релевантность: {medical_relevance:.2%}"
                    f"\nИтоговая релевантность: {final_score:.2%}"
                    f"\nНайденные термины: {', '.join(medical_terms)}"
                    f"\nИсточник: стр. {doc.metadata.get('page', 'н/д')}"
                )

                # Добавление результата в общий список
                all_results.append(result)
                
        except Exception as e:
            rag_logger.error(f"Ошибка при поиске в категории {category}: {e}")
            continue
    
    # Сортировка результатов по релевантности (по убыванию)
    all_results.sort(key=lambda x: x.score, reverse=True)
    
    # Формируем итоговый контекст
    context = "\n\nРелевантная информация из медицинской литературы:\n"
    rag_logger.info(f"\n{'='*50}\nИтоговый контекст:")

    # Добавление релевантных фрагментов в текст
    for i, result in enumerate(all_results[:n_results], 1):
        medical_terms_str = ', '.join(result.medical_terms) if result.medical_terms else 'не найдены'

        # Форматирование текста результата
        chunk_text = (
            f"\nИз раздела {result.category}"
            f" (релевантность: {result.score:.1%}):\n"
            f"{result.content}\n"
            f"Источник: стр. {result.metadata.get('page', 'н/д')}\n"
            f"Медицинские термины: {medical_terms_str}\n"
            f"{'-'*40}"
        )
        context += chunk_text
        rag_logger.info(f"\nЧанк {i} добавлен в итоговый контекст")
        rag_logger.info(f"Категория: {result.category}")
        rag_logger.info(f"Релевантность: {result.score:.1%}")
        rag_logger.info(f"Длина текста: {len(result.content)} символов")
    
    rag_logger.info(f"\nОбщая длина контекста: {len(context)} символов")
    rag_logger.info(f"{'='*50}\n")
    return context # Возврат готового контекста