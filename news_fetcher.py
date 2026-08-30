import feedparser
import re
from datetime import datetime, timezone

RSS_FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "PC Gamer": "https://www.pcgamer.com/rss/",
}


def clean_text(text):
    """Clean text for easier comparison."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def similarity_score(title1, title2):
    """Simple title similarity check."""
    words1 = set(clean_text(title1).split())
    words2 = set(clean_text(title2).split())

    if not words1 or not words2:
        return 0

    common = words1.intersection(words2)
    return len(common) / min(len(words1), len(words2))


def calculate_score(article):
    """Score an article based on source, freshness and keywords."""
    title = article["title"].lower()

    score = 0

    # Reliable / primary sources get higher scores
    source_scores = {
        "OpenAI": 30,
        "Google AI": 30,
        "TechCrunch AI": 25,
        "The Verge AI": 23,
        "PC Gamer": 20,
    }

    score += source_scores.get(article["source"], 10)

    # Important AI keywords
    important_keywords = [
        "openai",
        "anthropic",
        "google",
        "gemini",
        "chatgpt",
        "ai",
        "artificial intelligence",
        "nvidia",
        "claude",
        "model",
        "launch",
        "announces",
        "new",
        "release",
        "lawsuit",
        "acquisition",
    ]

    for keyword in important_keywords:
        if keyword in title:
            score += 5

    # Gaming keywords
    gaming_keywords = [
        "elden ring",
        "playstation",
        "xbox",
        "nintendo",
        "steam",
        "game",
        "gaming",
        "fps",
        "rpg",
    ]

    for keyword in gaming_keywords:
        if keyword in title:
            score += 3

    return score


def fetch_news():
    print("=" * 70)
    print("AI NEWS ENGINE - SMART NEWS FILTER")
    print("=" * 70)

    all_articles = []

    # Fetch RSS feeds
    for source, url in RSS_FEEDS.items():

        print(f"\nFetching: {source}")

        try:
            feed = feedparser.parse(url)

            for article in feed.entries[:10]:

                title = article.get("title", "").strip()
                link = article.get("link", "").strip()

                if not title or not link:
                    continue

                published = article.get(
                    "published",
                    article.get("updated", "Unknown date")
                )

                all_articles.append({
                    "source": source,
                    "title": title,
                    "link": link,
                    "published": published,
                })

        except Exception as error:
            print(f"ERROR: {error}")

    print("\n" + "=" * 70)
    print(f"RAW ARTICLES FOUND: {len(all_articles)}")
    print("=" * 70)

    # Remove duplicate / very similar titles
    unique_articles = []

    for article in all_articles:

        duplicate = False

        for existing in unique_articles:

            similarity = similarity_score(
                article["title"],
                existing["title"]
            )

            if similarity >= 0.60:
                duplicate = True
                break

        if not duplicate:
            unique_articles.append(article)

    print(f"AFTER DUPLICATE FILTER: {len(unique_articles)}")

    # Score articles
    for article in unique_articles:
        article["score"] = calculate_score(article)

    # Sort by score
    unique_articles.sort(
        key=lambda article: article["score"],
        reverse=True
    )

    # Select top 4
    top_articles = unique_articles[:4]

    print("\n" + "=" * 70)
    print("TOP STORIES")
    print("=" * 70)

    for index, article in enumerate(top_articles, start=1):

        print(f"\n#{index}")
        print(f"SCORE: {article['score']}")
        print(f"SOURCE: {article['source']}")
        print(f"TITLE: {article['title']}")
        print(f"DATE: {article['published']}")
        print(f"LINK: {article['link']}")

    print("\n" + "=" * 70)
    print("NEWS SELECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    fetch_news()
