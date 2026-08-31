import os
import feedparser
from datetime import datetime

from google import genai


RSS_FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "PC Gamer": "https://www.pcgamer.com/rss/",
}


GEMINI_MODEL = "gemini-3.6-flash"

OUTPUT_DIR = "articles"



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

        for item in feed.entries[:3]:

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
Write a professional Persian technology news article.

Title:
{article['title']}

Source:
{article['source']}

URL:
{article['link']}

Rules:
- Natural Persian
- No invented information
- Professional journalism style
- Include headline, summary and article body
"""


    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )


    return response.text



def save_article(
    article,
    content
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


    filename = (
        datetime.now()
        .strftime("%Y-%m-%d-%H-%M")
        +
        ".md"
    )


    path = os.path.join(
        OUTPUT_DIR,
        filename
    )


    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "# "
            +
            article["title"]
            +
            "\n\n"
        )

        file.write(content)


    print(
        "Saved:",
        path
    )



def main():

    client = create_client()


    articles = fetch_news()


    article = articles[0]


    print(
        "Generating:",
        article["title"]
    )


    content = generate_article(
        client,
        article
    )


    save_article(
        article,
        content
    )



if __name__ == "__main__":
    main()
