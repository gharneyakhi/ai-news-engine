import os
import feedparser

from google import genai


RSS_FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "PC Gamer": "https://www.pcgamer.com/rss/",
}


GEMINI_MODEL = "gemini-3.6-flash"


def create_client():

    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "Missing GEMINI_API_KEY"
        )

    return genai.Client(
        api_key=api_key
    )



def fetch_news():

    articles = []

    for source, url in RSS_FEEDS.items():

        print("Fetching:", source)

        feed = feedparser.parse(url)

        for item in feed.entries[:5]:

            title = item.get(
                "title",
                ""
            )

            link = item.get(
                "link",
                ""
            )

            if title and link:

                articles.append({
                    "source": source,
                    "title": title,
                    "link": link
                })

    return articles



def generate_article(
    client,
    article
):

    prompt = f"""
Write a Persian technology news article.

Title:
{article['title']}

Source:
{article['source']}

URL:
{article['link']}

Rules:
- Write natural Persian.
- Do not invent facts.
- Write like a professional news website.
- Include headline and summary.
"""


    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )


    return response.text



def main():

    print("=" * 60)
    print("AI ARTICLE GENERATOR TEST")
    print("=" * 60)


    client = create_client()


    articles = fetch_news()


    article = articles[0]


    print(
        "Generating:",
        article["title"]
    )


    result = generate_article(
        client,
        article
    )


    print()
    print(result)



if __name__ == "__main__":
    main()
