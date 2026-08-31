import os
from google import genai

GEMINI_MODEL = "gemini-3.6-flash"


def create_client():
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")

    return genai.Client(api_key=api_key)


def main():
    print("=" * 60)
    print("ARTICLE GENERATOR STARTED")
    print("=" * 60)

    client = create_client()

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents="Say hello in Persian"
    )

    print(response.text)


if __name__ == "__main__":
    main()
