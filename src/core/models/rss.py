import feedparser
from src.core.storage.rss_storage import RSSStorage

# 初始化 RSS 存储
rss_storage = RSSStorage()

def ParseRss(url):
    feed = feedparser.parse(url)
    print(feed.entries)
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
    """
    根据已存储的RSS URL获取数据并存储
    返回: 包含每个URL获取到的数据的字典
    """
    rss_urls = rss_storage.get_all_rss_urls()
    print(rss_urls)
    entries = {}
    for rss_source in rss_urls:
        url = rss_source["url"]
        try:
            feed_entries = ParseRss(url)
            entries[url] = feed_entries
        except Exception as e:
            print(f"获取RSS数据时出错: {e}")
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
    获取所有RSS feed，按发布日期从新到旧排序
    limit: 返回结果数量
    """
    return rss_storage.get_all_feeds(limit)

def add_rss_url(url, name=None):
    """
    添加RSS URL到存储
    url: RSS源的URL
    name: 可选，RSS源的名称
    返回: 添加成功返回True，已存在返回False
    """
    return rss_storage.store_rss_url(url, name)

def get_rss_urls():
    """
    获取所有存储的RSS URL
    返回: URL列表 [{"url": "http://...", "name": "源名称"}, ...]
    """
    return rss_storage.get_all_rss_urls()

def delete_rss_url(url):
    """
    删除RSS URL
    url: 要删除的RSS URL
    返回: 删除成功返回True，不存在返回False
    """
    return rss_storage.delete_rss_url(url)
