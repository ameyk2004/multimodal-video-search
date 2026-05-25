import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("No GEMINI_API_KEY found")
else:
    print("Key found:", GEMINI_API_KEY[:5] + "...")

genai.configure(api_key=GEMINI_API_KEY)
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = "Translate this to Marathi: Devotion to God"
    response = model.generate_content(prompt)
    print("Success:", response.text)
except Exception as e:
    print("Error:", e)
