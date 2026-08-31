```python
import os
import time
from google import genai


# ============================================================
# CONFIGURATION
# ============================================================

PRIMARY_MODEL = "gemini-3.6-flash"

# مدل پشتیبان؛ اگر مدل اصلی موقتاً 503 بدهد
BACKUP_MODELS = [
    "gemini-3.5-flash-lite",
]

MAX_RETRIES = 4
RETRY_DELAY = 8


# ============================================================
# CREATE GEMINI CLIENT
# ============================================================

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. "
        "Check GitHub Actions Secrets."
    )

client = genai.Client(api_key=api_key)


# ============================================================
# TEST GEMINI
# ============================================================

def test_model(model_name):

    print("=" * 70)
    print(f"TESTING MODEL: {model_name}")
    print("=" * 70)

    prompt = """
Reply with exactly:

Gemini connection successful.
"""

    for attempt in range(1, MAX_RETRIES + 1):

        print(
            f"Attempt {attempt}/{MAX_RETRIES}..."
        )

        try:

            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            if response.text:

                print("\nSUCCESS!")
                print("-" * 70)
                print(response.text)
                print("-" * 70)

                return True

            print("Gemini returned an empty response.")

        except Exception as error:

            error_text = str(error)

            print(
                f"ERROR: {error_text}"
            )

            # 503 = temporary server overload
            if "503" in error_text or "UNAVAILABLE" in error_text:

                if attempt < MAX_RETRIES:

                    wait_time = RETRY_DELAY * attempt

                    print(
                        f"Temporary server overload."
                    )

                    print(
                        f"Waiting {wait_time} seconds before retry..."
                    )

                    time.sleep(wait_time)

                else:

                    print(
                        "Maximum retries reached."
                    )

            else:

                # برای خطاهای غیرموقت، بی‌دلیل retry نمی‌کنیم
                print(
                    "This does not look like a temporary 503 error."
                )

                break

    return False


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("GEMINI CONNECTION TEST")
    print("=" * 70)
    print()

    # --------------------------------------------------------
    # Try primary model
    # --------------------------------------------------------

    if test_model(PRIMARY_MODEL):

        print()
        print("=" * 70)
        print("GEMINI TEST PASSED")
        print("=" * 70)

        return

    # --------------------------------------------------------
    # Try backup models
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("PRIMARY MODEL FAILED")
    print("TRYING BACKUP MODELS...")
    print("=" * 70)

    for model in BACKUP_MODELS:

        if test_model(model):

            print()
            print("=" * 70)
            print("BACKUP MODEL TEST PASSED")
            print("=" * 70)

            return

    # --------------------------------------------------------
    # Everything failed
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("GEMINI TEST FAILED")
    print("=" * 70)

    raise RuntimeError(
        "All Gemini models failed."
    )


if __name__ == "__main__":
    main()
```
