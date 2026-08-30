import feedparser
from datetime import datetime, timezone

RSS_FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "PC Gamer": "https://www.pcgamer.com/rss/",
}


def fetch_news():
    print("=" * 70)
    print("AI NEWS ENGINE")
    print("Fetching latest English news...")
    print("=" * 70)

    total = 0

    for source, url in RSS_FEEDS.items():
        print(f"\nSOURCE: {source}")
        print("-" * 70)

        try:
            feed = feedparser.parse(url)

            if not feed.entries:
                print("No articles found.")
                continue

            for article in feed.entries[:5]:
                title = article.get("title", "No title")
                link = article.get("link", "No link")

                published = article.get(
                    "published",
                    article.get("updated", "Unknown date")
                )

                print(f"TITLE: {title}")
                print(f"DATE:  {published}")
                print(f"LINK:  {link}")
                print()

                total += 1

        except Exception as error:
            print(f"ERROR: {error}")

    print("=" * 70)
    print(f"TOTAL ARTICLES FOUND: {total}")
    print("=" * 70)


if __name__ == "__main__":
    fetch_news()
