import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()
client = InferenceClient(token=os.getenv("HF_API_KEY"))
res = client.feature_extraction(text="namaskar", model="BAAI/bge-m3")
print(type(res))
try:
    print(len(res), len(res[0]))
except:
    pass
