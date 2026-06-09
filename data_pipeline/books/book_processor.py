import os
import json
import logging
import glob
import fitz  # PyMuPDF
import io
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)

class BookProcessor:
    """
    Reads PDFs from input_books directory and extracts text page-by-page.
    Uses Tesseract OCR to correctly extract legacy Marathi font text.
    Outputs JSON files to books_output directory.
    """
    def __init__(self, input_dir="data_pipeline/books/input_books", output_dir="data_pipeline/books/books_output"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def process_all(self):
        pdf_files = glob.glob(os.path.join(self.input_dir, "*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {self.input_dir}")
        
        for filepath in pdf_files:
            self.process_pdf(filepath)
            
    def process_pdf(self, filepath: str):
        book_name = os.path.splitext(os.path.basename(filepath))[0]
        out_path = os.path.join(self.output_dir, f"{book_name}.json")
        
        if os.path.exists(out_path):
            logger.info(f"Skipping {book_name} - output already exists.")
            return
            
        logger.info(f"Processing PDF via OCR: {book_name}")
        pages_data = []
        
        try:
            doc = fitz.open(filepath)
            total_pages = len(doc)
            
            # Helper function for parallel processing
            def process_single_page(page_num):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=250) # Slightly reduced dpi for speed without losing accuracy
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))
                
                text = pytesseract.image_to_string(pil_image, lang='mar').strip()
                return {
                    "page_number": page_num + 1,
                    "text": text,
                    "book_name": book_name
                }

            import concurrent.futures
            # Tesseract spawns separate processes, so ThreadPoolExecutor bypasses the GIL
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                # Map preserves order
                results = list(executor.map(process_single_page, range(total_pages)))
                
            pages_data.extend(results)
                
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(pages_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Successfully processed {book_name} - {len(pages_data)} pages.")
        except Exception as e:
            logger.error(f"Failed to process PDF {book_name}: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    processor = BookProcessor()
    processor.process_all()
