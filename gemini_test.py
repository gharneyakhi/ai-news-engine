import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key: raise RuntimeError("GEMINI_API_KEY is missing.")

client = genai.Client(api_key=api_key)

print("=" * 70)
print("GEMINI CONNECTION TEST")
print("=" * 70)

response = client.models.generate_content(
model="gemini-3.6-flash",
contents="Reply with exactly: Gemini connection successful."
)

print()
print("SUCCESS!")
print("-" * 70)
print(response.text)
print("-" * 70)
print("=" * 70)
print("GEMINI TEST PASSED")
print("=" * 70)
