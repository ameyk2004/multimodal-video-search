import os
from google import genai
from google.genai import types

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set")
        return
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents='test',
        )
        print("gemini-2.0-flash successful:", response.text)
    except Exception as e:
        print("gemini-2.0-flash error:", e)

    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents='test',
        )
        print("gemini-1.5-flash successful:", response.text)
    except Exception as e:
        print("gemini-1.5-flash error:", e)
        
    try:
        response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents='test',
        )
        print("gemini-1.5-pro successful:", response.text)
    except Exception as e:
        print("gemini-1.5-pro error:", e)

if __name__ == '__main__':
    main()
