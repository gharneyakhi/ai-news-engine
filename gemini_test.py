import os
import time
from google import genai

PRIMARY_MODEL = "gemini-3.6-flash"

BACKUP_MODELS = [
"gemini-3.5-flash-lite",
]

MAX_RETRIES = 4
RETRY_DELAY = 8

def create_client():
api_key = os.environ.get("GEMINI_API_KEY")

```
if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Check GitHub Actions Secrets."
    )

return genai.Client(api_key=api_key)
```

def test_model(client, model_name):
print("=" * 70)
print(f"TESTING MODEL: {model_name}")
print("=" * 70)

```
prompt = "Reply with exactly: Gemini connection successful."

for attempt in range(1, MAX_RETRIES + 1):
    print(f"Attempt {attempt}/{MAX_RETRIES}...")

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        if response.text:
            print()
            print("SUCCESS!")
            print("-" * 70)
            print(response.text)
            print("-" * 70)
            return True

        print("Gemini returned an empty response.")

    except Exception as error:
        error_text = str(error)

        print(f"ERROR: {error_text}")

        if "503" in error_text or "UNAVAILABLE" in error_text:
            if attempt < MAX_RETRIES:
                wait_time = RETRY_DELAY * attempt

                print(
                    f"Temporary server overload. "
                    f"Waiting {wait_time} seconds before retry..."
                )

                time.sleep(wait_time)
            else:
                print("Maximum retries reached.")

        else:
            print("Non-retryable error detected.")
            break

return False
```

def main():
print()
print("=" * 70)
print("GEMINI CONNECTION TEST")
print("=" * 70)
print()

```
client = create_client()

print("Trying primary model...")
print()

if test_model(client, PRIMARY_MODEL):
    print()
    print("=" * 70)
    print("GEMINI TEST PASSED")
    print("=" * 70)
    return

print()
print("=" * 70)
print("PRIMARY MODEL FAILED")
print("TRYING BACKUP MODELS...")
print("=" * 70)
print()

for model in BACKUP_MODELS:
    if test_model(client, model):
        print()
        print("=" * 70)
        print("BACKUP MODEL TEST PASSED")
        print("=" * 70)
        return

print()
print("=" * 70)
print("GEMINI TEST FAILED")
print("=" * 70)

raise RuntimeError("All Gemini models failed.")
```

if **name** == "**main**":
main()
