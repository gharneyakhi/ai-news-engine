import feedparser


RSS_FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "PC Gamer": "https://www.pcgamer.com/rss/",
}


def fetch_news():

    articles = []

    for source, url in RSS_FEEDS.items():

        print("Fetching:", source)

        feed = feedparser.parse(url)

        for item in feed.entries[:5]:

            articles.append({
                "source": source,
                "title": item.get("title", ""),
                "link": item.get("link", "")
            })

    return articles


def main():

    print("=" * 60)
    print("NEWS FETCH TEST")
    print("=" * 60)

    articles = fetch_news()

    print("TOTAL:", len(articles))

    for article in articles[:10]:
        print()
        print(article["source"])
        print(article["title"])


if __name__ == "__main__":
    main()
