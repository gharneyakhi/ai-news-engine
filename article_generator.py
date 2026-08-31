import feedparser
from datetime import datetime, timezone, timedelta


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

        for item in feed.entries[:10]:

            title = item.get("title", "")
            link = item.get("link", "")

            if title and link:

                articles.append({
                    "source": source,
                    "title": title,
                    "link": link,
                    "score": 0
                })

    return articles



def score_article(article):

    title = article["title"].lower()

    score = 0

    important_words = [
        "openai",
        "gemini",
        "ai",
        "launch",
        "new",
        "release",
        "announced",
        "model"
    ]

    for word in important_words:

        if word in title:
            score += 5


    if article["source"] in [
        "OpenAI",
        "Google AI"
    ]:
        score += 10


    return score



def select_top_articles(articles):

    for article in articles:

        article["score"] = score_article(article)


    articles.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    return articles[:3]



def main():

    print("=" * 60)
    print("SMART NEWS SELECTION")
    print("=" * 60)


    articles = fetch_news()


    selected = select_top_articles(
        articles
    )


    print()
    print("TOP STORIES")
    print("=" * 60)


    for i, article in enumerate(
        selected,
        start=1
    ):

        print(
            i,
            article["score"],
            article["source"],
            article["title"]
        )



if __name__ == "__main__":
    main()
