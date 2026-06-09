import fitz
import os
import io
from PIL import Image
from google import genai
from dotenv import load_dotenv

load_dotenv()

def test_ocr():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    doc = fitz.open("data_pipeline/books/input_books/Jaag.pdf")
    page = doc.load_page(3) # Page 4
    
    # Render page to image
    pix = page.get_pixmap(dpi=150)
    img_data = pix.tobytes("png")
    pil_image = Image.open(io.BytesIO(img_data))
    
    print("Sending image to Gemini for OCR...")
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[
            "Extract all the Marathi text from this image exactly as it is written. Preserve the layout where possible. Do not add any markdown formatting, just the raw text.",
            pil_image
        ]
    )
    print("--- Extracted Text ---")
    print(response.text)

if __name__ == "__main__":
    test_ocr()
