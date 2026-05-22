import os
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

def test_gemini_api():
    print("Loading environment variables from .env...")
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env file or environment.")
        return
    
    # Hide the full key for security, just show the start/end
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "INVALID_LENGTH"
    print(f"✅ Found API Key: {masked_key}")
    
    try:
        print("Initializing Gemini Client...")
        client = genai.Client(api_key=api_key)
        
        # We use gemini-2.5-flash as you have migrated to it
        model_name = "gemini-2.5-flash"
        print(f"Sending a test request to {model_name}...")
        
        response = client.models.generate_content(
            model=model_name,
            contents="Hello! Please reply with a short sentence to confirm you are working."
        )
        
        print("\n🎉 Success! The API key is valid and working.")
        print("-" * 40)
        print("Response from Gemini:")
        print(response.text.strip())
        print("-" * 40)
        
    except APIError as e:
        print("\n❌ API Error Occurred!")
        print(f"Error Code: {e.code}")
        print(f"Error Message: {e.message}")
        if "quota" in str(e).lower() or e.code == 429:
            print("\n💡 Diagnosis: You have exceeded your quota/rate limits for this API key. You might need to check your Google Cloud Console billing or wait for the quota to reset.")
        elif e.code == 403:
            print("\n💡 Diagnosis: The API key might be invalid, disabled, or lacks permissions for this model.")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        if "quota" in str(e).lower() or "429" in str(e):
             print("\n💡 Diagnosis: You have exceeded your quota/rate limits for this API key. You might need to check your Google Cloud Console billing or wait for the quota to reset.")

if __name__ == "__main__":
    test_gemini_api()
