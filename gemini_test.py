import os
import time
from google import genai

PRIMARY_MODEL = "gemini-3.6-flash"
BACKUP_MODEL = "gemini-3.5-flash-lite"
MAX_RETRIES = 4
RETRY_DELAY = 8

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("=" * 70)
print("GEMINI CONNECTION TEST")
print("=" * 70)

model = PRIMARY_MODEL
success = False

for attempt in range(MAX_RETRIES):

```
print("Model:", model)
print("Attempt:", attempt + 1, "of", MAX_RETRIES)

try:
    response = client.models.generate_content(
        model=model,
        contents="Reply with exactly: Gemini connection successful."
    )
    print(response.text)
    success = True
    break
except Exception as error:
    print("ERROR:", error)
    time.sleep(RETRY_DELAY)
```

if success == False:

```
print("Primary model failed.")
print("Trying backup model.")

model = BACKUP_MODEL

for attempt in range(MAX_RETRIES):

    print("Model:", model)
    print("Attempt:", attempt + 1, "of", MAX_RETRIES)

    try:
        response = client.models.generate_content(
            model=model,
            contents="Reply with exactly: Gemini connection successful."
        )
        print(response.text)
        success = True
        break
    except Exception as error:
        print("ERROR:", error)
        time.sleep(RETRY_DELAY)
```

if success == False:
raise RuntimeError("All Gemini attempts failed.")

print("=" * 70)
print("GEMINI TEST PASSED")
print("=" * 70)
