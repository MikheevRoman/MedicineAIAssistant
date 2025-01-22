import os
import glob
import logging
import threading
import hashlib
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from typing import Dict, Tuple, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from text_preprocessing import clean_text, create_medical_text_splitter
from embeddings_handler import CustomEmbeddings
from logger_config import setup_logger

setup_logger()
logger = logging.getLogger('pdf_processor')

NUMBER_OF_CORES = max(1, multiprocessing.cpu_count() - 1)
VECTOR_STORE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_stores")
PDF_CATEGORIES = {
    'акушерство': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'medical_books/obstetrics/*.pdf'),
    'кардиология': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'medical_books/cardiology/*.pdf'),
    'стоматология': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'medical_books/dentistry/*.pdf'),
    'педиатрия': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'medical_books/pediatrics/*.pdf'),
    'терапия': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'medical_books/therapy/*.pdf'),
    'офтальмология': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'medical_books/ophthalmology/*.pdf'),
    'неврология': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'medical_books/neurology/*.pdf'),
    'хирургия': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'medical_books/surgery/*.pdf')
}

def calculate_files_hash(file_paths: list) -> str:
    """Вычисляет общий хеш для списка файлов"""
    hasher = hashlib.md5()
    for file_path in sorted(file_paths):  # Сортируем для стабильности хеша
        try:
            with open(file_path, 'rb') as f:
                # Читаем файл блоками для экономии памяти
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {file_path}: {e}")
    return hasher.hexdigest()

def get_category_hash(category: str, file_paths: list) -> str:
    """Создает уникальный идентификатор для категории на основе содержимого файлов"""
    files_hash = calculate_files_hash(file_paths)
    
    # Транслитерация категории
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    
    category_en = ''.join(translit_map.get(c.lower(), c) for c in category)
    
    # Создаем идентификатор только из хеша файлов
    category_id = f"{category_en}_{files_hash[:8]}"
    return category_id

def process_single_pdf(args: Tuple[str, str, str]) -> Optional[Tuple[str, FAISS]]:
    """Обрабатывает один PDF файл и возвращает его векторное хранилище"""
    category, pdf_path, category_id = args
    vector_store_path = os.path.join(VECTOR_STORE_DIR, f"{category_id}.faiss")
    index_path = os.path.join(VECTOR_STORE_DIR, f"{category_id}.pkl")
    embeddings = CustomEmbeddings()
    
    try:
        # Проверяем существование обоих файлов
        if not (os.path.exists(vector_store_path) and os.path.exists(index_path)):
            logger.info(f"Обработка файла {pdf_path}")
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            if documents:
                # Очищаем и подготавливаем текст
                for doc in documents:
                    doc.page_content = clean_text(doc.page_content)
                
                # Используем оптимизированный разделитель
                text_splitter = create_medical_text_splitter()
                texts = text_splitter.split_documents(documents)
                
                logger.info(f"Файл {pdf_path} разбит на {len(texts)} чанков")
                logger.info(f"Средний размер чанка: {sum(len(t.page_content) for t in texts) / len(texts):.0f} символов")
                
                vector_store = FAISS.from_documents(texts, embeddings)
                # Сохраняем оба файла
                vector_store.save_local(
                    folder_path=VECTOR_STORE_DIR,
                    index_name=category_id
                )
                logger.info(f"Сохранены эмбеддинги для {category_id}")
                
                return category, vector_store
        else:
            logger.info(f"Загрузка существующих эмбеддингов для {category_id}")
            try:
                vector_store = FAISS.load_local(
                    folder_path=VECTOR_STORE_DIR,
                    index_name=category_id,
                    embeddings=embeddings,
                    allow_dangerous_deserialization=True
                )
                return category, vector_store
            except Exception as e:
                logger.error(f"Ошибка при загрузке эмбеддингов {category_id}: {e}")
                # Если не удалось загрузить, удаляем поврежденные файлы
                try:
                    os.remove(vector_store_path)
                    os.remove(index_path)
                except:
                    pass
                return None
            
    except Exception as e:
        logger.error(f"Ошибка при обработке {pdf_path}: {e}")
        return None

def load_and_process_pdfs() -> Dict[str, FAISS]:
    """Загружает PDF файлы по категориям и создает векторные хранилища"""
    vector_stores = {}
    processing_tasks = []
    
    logger.info(f"Запуск обработки PDF файлов в {NUMBER_OF_CORES} потоков")
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    
    # Собираем все задачи для обработки
    for category, path_pattern in PDF_CATEGORIES.items():
        pdf_files = glob.glob(path_pattern)
        
        if not pdf_files:
            logger.warning(f"PDF файлы не найдены для категории {category}")
            continue
        
        # Получаем уникальный идентификатор для категории
        category_id = get_category_hash(category, pdf_files)
        
        # Добавляем задачу для каждого файла
        for pdf_path in pdf_files:
            processing_tasks.append((category, pdf_path, category_id))
    
    total_tasks = len(processing_tasks)
    logger.info(f"Всего файлов для обработки: {total_tasks}")
    
    # Создаем словарь для хранения мьютексов по категориям
    category_locks = {category: threading.Lock() for category in PDF_CATEGORIES.keys()}
    
    def process_result(result: Optional[Tuple[str, FAISS]]):
        if result is None:
            return
        
        category, vector_store = result
        with category_locks[category]:
            if category not in vector_stores:
                vector_stores[category] = vector_store
            else:
                vector_stores[category].merge_from(vector_store)
    
    # Запускаем обработку в пуле потоков
    completed_tasks = 0
    with ThreadPoolExecutor(max_workers=NUMBER_OF_CORES) as executor:
        futures = [executor.submit(process_single_pdf, task) for task in processing_tasks]
        for future in futures:
            try:
                result = future.result()
                if result:
                    process_result(result)
                completed_tasks += 1
                logger.info(f"Прогресс обработки: {completed_tasks}/{total_tasks} файлов ({completed_tasks/total_tasks*100:.1f}%)")
            except Exception as e:
                logger.error(f"Ошибка при обработке задачи: {e}")
    
    logger.info("Обработка PDF файлов завершена")
    return vector_stores 