import re
import feedparser
from flask import json
from src.core.models.chat import AIChat
from src.core.utils.config import RSS_SYSTEM_PROMPT
from src.core.storage.rss_storage import RSSStorage

# 初始化 RSS 存储
rss_storage = RSSStorage()
url = "http://localhost:5000/chat" 
aiChat = AIChat(modelType="deepseek", system_prompt=RSS_SYSTEM_PROMPT)

def ParseRss(url):
    feed = feedparser.parse(url)
    entries = []
    for entry in feed.entries:
        entry_data = {
            'title': entry.title,
            'link': entry.link,
            'summary': entry.summary,
            'content': entry.content,
            'published': entry.published,
            'source': url,
        }
        if not rss_storage.check_has_feed(entry_data):
            entries.append(entry_data)
    
    # 如果没有新条目，直接返回
    if not entries:
        return []
    
    aiResponse = aiChat.getResponse(json.dumps(entries))
    
    processed_entries = []
    try:
        # 解析 AI 返回的 JSON 数据
        ai_data = json.loads(aiResponse)
        
        # 处理每个 AI 生成的条目
        for ai_entry in ai_data:
            # 在原始 entries 中查找匹配的条目
            original_entry =  [item for item in entries if item["link"] == ai_entry.get('link')][0]
           
            if original_entry:
                # 创建包含 AI 生成内容和原始发布信息的新条目
                processed_entry = {
                    'title': ai_entry.get('AITitle'),
                    'link': ai_entry.get('link'),
                    'summary': ai_entry.get('AISummary'),
                    'source': url,
                    'published': original_entry.get('published'),  # 包含原始条目的所有信息
                }
                processed_entries.append(processed_entry)
                
                # 存储到 RSS 存储中
                rss_storage.store_feed(processed_entry)
    
    except Exception as e:
        print(f"处理 JSON 时出错: {e}")
        print(f"原始响应: {aiResponse}")
    
    return processed_entries

def OutputRss():
    """
    根据已存储的RSS URL获取数据并存储
    返回: 包含每个URL获取到的数据的字典
    """
    rss_urls = rss_storage.get_all_rss_urls()
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
