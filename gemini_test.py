import os
import time
from google import genai

PRIMARY_MODEL = "gemini-3.6-flash"
BACKUP_MODEL = "gemini-3.5-flash-lite"

MAX_RETRIES = 4
RETRY_DELAY = 8

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
raise RuntimeError("GEMINI_API_KEY is missing.")

client = genai.Client(api_key=api_key)

prompt = "Reply with exactly: Gemini connection successful."

models = [
PRIMARY_MODEL,
BACKUP_MODEL
]

success = False

for model in models:
print("=" * 70)
print("TESTING MODEL:", model)
print("=" * 70)

```
for attempt in range(1, MAX_RETRIES + 1):
    print("Attempt", attempt, "of", MAX_RETRIES)

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )

        if response.text:
            print()
            print("SUCCESS!")
            print(response.text)
            success = True
            break

    except Exception as error:
        print("ERROR:", error)

        error_text = str(error)

        if "503" in error_text or "UNAVAILABLE" in error_text:
            if attempt < MAX_RETRIES:
                wait_time = RETRY_DELAY * attempt

                print("Temporary server problem.")
                print("Waiting", wait_time, "seconds...")

                time.sleep(wait_time)
            else:
                print("Maximum retries reached.")
        else:
            print("Non-retryable error.")
            break

if success:
    break
```

if not success:
raise RuntimeError("All Gemini model attempts failed.")

print()
print("=" * 70)
print("GEMINI TEST PASSED")
print("=" * 70)
