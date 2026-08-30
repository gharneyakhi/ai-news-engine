import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="به فارسی روان فقط بنویس: اتصال Gemini با موفقیت انجام شد."
)

print("=" * 60)
print(response.text)
print("=" * 60)
