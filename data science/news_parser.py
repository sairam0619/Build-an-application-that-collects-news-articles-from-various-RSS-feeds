import feedparser
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import csv

# Step 1: Setting up the database
Base = declarative_base()

class NewsArticle(Base):
    __tablename__ = 'news_articles'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)
    publication_date = Column(String)
    source_url = Column(String)
    category = Column(String)

engine = create_engine('sqlite:///news_articles.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Step 2: Parsing RSS feeds
rss_feed_urls = [
    "http://rss.cnn.com/rss/cnn_topstories.rss",
    "http://qz.com/feed",
    "http://feeds.foxnews.com/foxnews/politics",
    "http://feeds.reuters.com/reuters/businessNews",
    "http://feeds.feedburner.com/NewshourWorld",
    "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml"
]

def parse_rss_feeds(feed_urls):
    articles = []
    for url in feed_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            article = {
                "title": entry.title,
                "content": getattr(entry, 'summary', None) or getattr(entry, 'description', None) or "",
                "publication_date": getattr(entry, 'published', None),  # Check if 'published' attribute exists
                "source_url": entry.link
            }
            articles.append(article)
    return articles


parsed_articles = parse_rss_feeds(rss_feed_urls)

# Step 3: Classifying articles
def classify_article(content):
    tokens = word_tokenize(content.lower())
    stop_words = set(stopwords.words('english'))
    if any(word in tokens for word in ['terrorism', 'protest', 'political unrest', 'riot']):
        return 'Terrorism/Protest/Political Unrest/Riot'
    elif any(word in tokens for word in ['positive', 'uplifting']):
        return 'Positive/Uplifting'
    elif 'natural disaster' in tokens:
        return 'Natural Disaster'
    else:
        return 'Others'

for article in parsed_articles:
    article['category'] = classify_article(article['content'])

# Step 4: Storing data in the database
def store_articles_in_database(articles):
    for article in articles:
        news_article = NewsArticle(
            title=article["title"],
            content=article["content"],
            publication_date=article["publication_date"],
            source_url=article["source_url"],
            category=article["category"]
        )
        session.add(news_article)
    session.commit()

store_articles_in_database(parsed_articles)
session.close()

# Step 5: Exporting data to CSV
def export_to_csv(articles, filename):
    keys = articles[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(articles)

export_to_csv(parsed_articles, 'news_articles.csv')
