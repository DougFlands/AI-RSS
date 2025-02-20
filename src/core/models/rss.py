import feedparser

from src.core.utils.config import getJsonConfig

def ParseRss(url):
    feed = feedparser.parse(url)
    entries = []
    for entry in feed.entries:
        entries.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'summary': entry.summary if 'summary' in entry else ''
        })
    return entries

def OutputRss():
    rss_url = getJsonConfig("rss_url")
    entries = {}
    for url in rss_url:
        try:
            feed_entries = ParseRss(url)
            entries[url] = feed_entries
        except Exception as e:
            print(f"An error occurred: {e}")
    return entries
