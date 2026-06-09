import os
import glob
import fitz  # PyMuPDF

INPUT_DIR = "data_pipeline/books/input_books"
OUTPUT_DIR = "frontend/public/books"

def extract_thumbnails():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_files = glob.glob(os.path.join(INPUT_DIR, "*.pdf"))
    
    if not pdf_files:
        print(f"No PDFs found in {INPUT_DIR}")
        return

    for pdf_path in pdf_files:
        book_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(OUTPUT_DIR, f"{book_name}.jpg")
        
        print(f"Extracting thumbnail for {book_name}...")
        try:
            doc = fitz.open(pdf_path)
            if len(doc) > 0:
                page = doc[0]
                # High resolution thumbnail
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                pix.save(output_path)
                print(f"✅ Saved thumbnail: {output_path}")
            else:
                print(f"❌ Document has no pages: {pdf_path}")
            doc.close()
        except Exception as e:
            print(f"❌ Failed to extract thumbnail for {pdf_path}: {e}")

if __name__ == "__main__":
    extract_thumbnails()
