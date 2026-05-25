import os
from dotenv import load_dotenv
from google import genai

def main():
    load_dotenv()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment or .env file.")
        return

    print(f"🔑 Loaded API Key: {api_key[:10]}...{api_key[-4:]}\n")
    print("Fetching available Gemini models (Text Generation)...\n")

    try:
        client = genai.Client(api_key=api_key)
        
        print(f"{'MODEL NAME':<35} | {'INPUT LIMIT':<15} | {'OUTPUT LIMIT':<15}")
        print("-" * 75)

        for model in client.models.list():
            # Exclude embeddings, legacy models, tuning models, and AQA
            if any(x in model.name for x in ["embedding", "text-bison", "chat-bison", "aqa", "tunedModels"]):
                continue
            
            # We want models that support generateContent (safely check)
            supported_methods = getattr(model, "supported_generation_methods", [])
            if supported_methods and "generateContent" not in supported_methods:
                continue

            # Safe extraction of token limits
            input_limit = getattr(model, "input_token_limit", "Unknown")
            output_limit = getattr(model, "output_token_limit", "Unknown")
            
            # Format nicely
            in_lim_str = f"{input_limit:,}" if isinstance(input_limit, int) else str(input_limit)
            out_lim_str = f"{output_limit:,}" if isinstance(output_limit, int) else str(output_limit)
            
            print(f"{model.name:<35} | {in_lim_str:<15} | {out_lim_str:<15}")
            
        print("\nNote: The API limits shown are the maximum context sizes for a single request.")
        print("Google does not expose 'remaining daily quota' via the list models API.")
        print("To check your exact rate limits (RPM/TPM) and remaining daily quota, please visit:")
        print("https://aistudio.google.com/app/plan_information")

    except Exception as e:
        print(f"\n❌ Failed to query Gemini API: {e}")

if __name__ == "__main__":
    main()
