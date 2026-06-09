import fitz
import io
import pytesseract
from PIL import Image

def test_local_ocr():
    # 1. Open PDF with PyMuPDF
    doc = fitz.open("data_pipeline/books/input_books/Jaag.pdf")
    page = doc.load_page(3) # Page 4 (index 3) has index/content
    
    # 2. Render page to image
    pix = page.get_pixmap(dpi=150)
    img_data = pix.tobytes("png")
    pil_image = Image.open(io.BytesIO(img_data))
    
    print("Running local Tesseract OCR (No LLMs, purely native/offline)...")
    # 3. Use Tesseract to extract Marathi text
    extracted_text = pytesseract.image_to_string(pil_image, lang='mar')
    
    print("--- Extracted Text ---")
    print(extracted_text.strip()[:1000]) # Print first 1000 characters

if __name__ == "__main__":
    test_local_ocr()
