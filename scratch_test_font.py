import os
import sys
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

sample_text = """OmJ
               (AmZ§X_` OrdZmgmR>r gmonr {dMmagyÌ§)
        S>m°. gwhmg noR>o
E_².E.,nrEM².S>r.(VÎdkmZ)"""

prompt = f"""This is Marathi text typed using a legacy ASCII font (like Shivaji or Kiran). 
Convert this into proper Unicode Devanagari Marathi.
Output ONLY the translated Devanagari text. Do not add any conversational text.

Text to convert:
{sample_text}
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
)

print(response.text)
