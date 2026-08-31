import os
import re
import time
import feedparser
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from google import genai


RSS_FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "PC Gamer": "https://www.pcgamer.com/rss/",
    "IGN": "https://feeds.feedburner.com/ign/all",
    "GameSpot": "https://www.gamespot.com/feeds/news/",
    "Eurogamer": "https://www.eurogamer.net/feed",
}


GEMINI_MODEL = "gemini-3.6-flash"

OUTPUT_DIR = "articles"

ARTICLES_PER_RUN = 3

MAX_ARTICLE_AGE_DAYS = 7

MAX_SOURCE_CHARS = 12000


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


def clean_text(text):

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def get_category(title, source):

    text = title.lower()

    gaming_words = [
        "game",
        "gaming",
        "playstation",
        "xbox",
        "nintendo",
        "steam",
        "elden ring",
        "gta",
        "grand theft auto",
        "fps",
        "rpg"
    ]

    ai_words = [
        "ai",
        "artificial intelligence",
        "openai",
        "chatgpt",
        "gemini",
        "claude",
        "nvidia",
        "machine learning"
    ]


    if any(
        word in text
        for word in gaming_words
    ):
        return "Gaming"


    if any(
        word in text
        for word in ai_words
    ):
        return "AI"


    if source in [
        "PC Gamer",
        "IGN",
        "GameSpot",
        "Eurogamer"
    ]:
        return "Gaming"


    return "Technology"


def parse_date(item):

    try:

        if item.get(
            "published_parsed"
        ):

            return datetime(
                *item.published_parsed[:6],
                tzinfo=timezone.utc
            )

        if item.get(
            "updated_parsed"
        ):

            return datetime(
                *item.updated_parsed[:6],
                tzinfo=timezone.utc
            )

    except Exception:

        pass


    return datetime.now(
        timezone.utc
    )
    def fetch_news():

    articles = []

    print("=" * 70)
    print("NEWS ENGINE - AI + GAMING MODE")
    print("=" * 70)


    for source, url in RSS_FEEDS.items():

        print(
            f"Fetching: {source}"
        )

        try:

            feed = feedparser.parse(
                url
            )

            for item in feed.entries[:10]:

                title = item.get(
                    "title",
                    ""
                ).strip()

                link = item.get(
                    "link",
                    ""
                ).strip()


                if not title or not link:
                    continue


                date = parse_date(
                    item
                )


                articles.append(
                    {
                        "source": source,
                        "title": title,
                        "link": link,
                        "date": date,
                        "category": get_category(
                            title,
                            source
                        )
                    }
                )


        except Exception as error:

            print(
                f"ERROR {source}: {error}"
            )


    print(
        f"RAW ARTICLES: {len(articles)}"
    )

    return articles



def filter_recent(
    articles
):

    now = datetime.now(
        timezone.utc
    )

    result = []


    for article in articles:

        age = now - article["date"]

        if age <= timedelta(
            days=MAX_ARTICLE_AGE_DAYS
        ):

            result.append(
                article
            )


    return result



def remove_duplicates(
    articles
):

    unique = []


    titles = set()


    for article in articles:

        key = clean_text(
            article["title"]
        )


        if key in titles:
            continue


        titles.add(
            key
        )

        unique.append(
            article
        )


    return unique



def select_articles(
    articles
):

    selected = []


    categories = [
        "AI",
        "Gaming",
        "Technology"
    ]


    for category in categories:

        for article in articles:

            if article["category"] == category:

                selected.append(
                    article
                )

                break



    return selected[:ARTICLES_PER_RUN]



def read_source_page(
    url
):

    print(
        f"Reading source: {url}"
    )


    try:

        headers = {
            "User-Agent":
            "Mozilla/5.0"
        }


        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        for tag in soup(
            [
                "script",
                "style",
                "nav",
                "footer"
            ]
        ):

            tag.decompose()


        paragraphs = []


        for p in soup.find_all(
            "p"
        ):

            text = p.get_text(
                " ",
                strip=True
            )


            if len(text) > 40:

                paragraphs.append(
                    text
                )


        content = "\n\n".join(
            paragraphs
        )


        return content[
            :MAX_SOURCE_CHARS
        ]


    except Exception as error:

        print(
            f"Source error: {error}"
        )

        return ""
        def build_prompt(article, source_text):

    return f"""
You are a professional Persian technology and gaming editor.

Write an original Persian news article.

Rules:
- Write fluent modern Persian.
- Do not translate word by word.
- Do not invent facts.
- Use only the provided source.
- Do not mention AI or these instructions.
- Keep game and technology names in English when useful.

Category:
{article["category"]}

Source:
{article["source"]}

Title:
{article["title"]}

URL:
{article["link"]}

Source text:
{source_text}


Return this format:

TITLE:

SUMMARY:

ARTICLE:

SEO_TITLE:

META_DESCRIPTION:

TAGS:
"""



def generate_article(
    client,
    article,
    source_text
):

    print(
        "-" * 70
    )

    print(
        "Generating:",
        article["title"]
    )


    prompt = build_prompt(
        article,
        source_text
    )


    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )


        return response.text


    except Exception as error:

        print(
            "Gemini error:",
            error
        )

        return None



def save_article(
    article,
    content
):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


    date = datetime.now().strftime(
        "%Y-%m-%d-%H-%M"
    )


    filename = (
        date
        +
        "-"
        +
        article["category"].lower()
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


        file.write(
            "Category: "
            +
            article["category"]
            +
            "\n\n"
        )


        file.write(
            "Source: "
            +
            article["source"]
            +
            "\n\n"
        )


        file.write(
            "URL: "
            +
            article["link"]
            +
            "\n\n"
        )


        file.write(
            "---\n\n"
        )


        file.write(
            content
        )


    print(
        "Saved:",
        path
    )



def main():

    client = create_client()


    articles = fetch_news()


    articles = remove_duplicates(
        articles
    )


    articles = filter_recent(
        articles
    )


    selected = select_articles(
        articles
    )


    print("=" * 70)

    print(
        "SELECTED:"
    )


    for item in selected:

        print(
            item["category"],
            "-",
            item["title"]
        )


    for article in selected:


        source_text = read_source_page(
            article["link"]
        )


        if not source_text:

            print(
                "No source text, skip"
            )

            continue


        content = generate_article(
            client,
            article,
            source_text
        )


        if content:

            save_article(
                article,
                content
            )


        time.sleep(
            3
        )


    print("=" * 70)

    print(
        "ARTICLE GENERATION COMPLETE"
    )



if __name__ == "__main__":

    main()
