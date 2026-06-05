"""
Main entry point for processing and enriching books.
To run: python data_pipeline/books_main.py
"""
import logging
from data_pipeline.books.book_processor import BookProcessor
from data_pipeline.books.book_chunk_processor import process_directory as process_chunks
from data_pipeline.books.book_enricher import BookEnricher

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    print("=== Phase 1: PDF Extraction ===")
    processor = BookProcessor()
    processor.process_all()
    
    print("\n=== Phase 2: Semantic Chunking (with precise page mapping) ===")
    process_chunks(input_dir="data_pipeline/books/books_output", output_dir="data_pipeline/books/processed_books_chunks")
    
    print("\n=== Phase 3: Metadata Enrichment (Gemini LLM) ===")
    enricher = BookEnricher()
    enricher.process_all()
    
    print("\nPipeline complete. Next steps:")
    print("1. Generate embeddings for processed_books_chunks using Colab or HuggingFace API.")
    print("2. Run scripts/qdrant/rebuild_books_collection.py to index into Qdrant.")
