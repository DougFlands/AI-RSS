import feedparser
from src.core.utils.config import getJsonConfig
from src.core.storage.rss_storage import RSSStorage

# 初始化 RSS 存储
rss_storage = RSSStorage()

def ParseRss(url):
    feed = feedparser.parse(url)
    entries = []
    for entry in feed.entries:
        entry_data = {
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'summary': entry.summary if 'summary' in entry else ''
        }
        # 存储到 Chroma
        rss_storage.store_feed({
            'title': entry_data['title'],
            'link': entry_data['link'],
            'pub_date': entry_data['published'],
            'description': entry_data['summary'],
            'source': url
        })
        entries.append(entry_data)
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

def search_rss_feeds(query, n_results=5):
    """
    搜索已存储的RSS feed
    query: 搜索关键词
    n_results: 返回结果数量
    """
    return rss_storage.search_feeds(query, n_results)

def get_all_rss_feeds(limit=20):
    """
    获取所有RSS feed，并按用户喜好排序
    limit: 返回结果数量
    """
    return rss_storage.get_all_feeds(limit)
