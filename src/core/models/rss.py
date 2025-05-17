import re
from venv import logger
import feedparser
from flask import json
from src.core.models.chat import AIChat
from src.core.utils.config import RSS_SYSTEM_PROMPT
from src.core.storage.rss_storage import RSSStorage
import logging
import ssl
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context
# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化 RSS 存储
rss_storage = RSSStorage()
aiChat = AIChat(modelType="deepseek", system_prompt=RSS_SYSTEM_PROMPT)

def parse_rss(url):
    feed = feedparser.parse(url)
    if len(feed.entries)  == 0:
        logger.warning(url)
        logger.warning(feed)
        
    entries = []
    for entry in feed.entries:
        # 处理日期格式，统一转换为ISO格式
        published_date = entry.published
        try:
            # 尝试解析不同格式的日期
            dt = None
            try:
                # RFC 822 格式，如 'Fri, 16 May 2025 17:07:00 +0800'
                dt = datetime.strptime(published_date, '%a, %d %b %Y %H:%M:%S %z')
            except ValueError:
                try:
                    # 尝试ISO格式，如 '2025-05-16T00:05:44Z'
                    dt = datetime.strptime(published_date, '%Y-%m-%dT%H:%M:%SZ')
                except ValueError:
                    try:
                        # 尝试其他常见格式
                        dt = datetime.strptime(published_date, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        dt = datetime.strptime(published_date, '%Y-%m-%d')
            
            # 统一转换为ISO格式
            if dt:
                published_date = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        except (ValueError, TypeError, AttributeError):
            # 如果解析失败，保留原始格式
            pass
            
        entry_data = {
            'title': entry.title,
            'link': entry.link,
            'summary': entry.summary,
            'content': entry.content,
            'published': published_date,
            'source': url,
        }
        if not rss_storage.check_has_feed(entry_data):
            entries.append(entry_data)
    
    # 如果没有新条目，直接返回
    if not entries:
        return []
    
    aiResponse = aiChat.get_response(json.dumps(entries))
    
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

def output_rss():
    """
    根据已存储的RSS URL获取数据并存储
    返回: 包含每个URL获取到的数据的字典
    """
    rss_urls = rss_storage.get_all_rss_urls()
    entries = {}
    for rss_source in rss_urls:
        url = rss_source["url"]
        try:
            feed_entries = parse_rss(url)
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
