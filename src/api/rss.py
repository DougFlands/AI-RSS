from flask import Blueprint, request, jsonify
from src.core.models.rss import OutputRss, search_rss_feeds, get_all_rss_feeds, ParseRss
from src.core.storage.rss_storage import RSSStorage
from datetime import datetime

rss_bp = Blueprint("rss", __name__, url_prefix="/rss")
rss_storage = RSSStorage()

@rss_bp.route('/story', methods=['POST'])
def GetStoryRss():
    data = request.get_json()
    # 验证参数
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query parameter'}), 400
    query = data['query']
    n_results = data.get('n_results', 5)  # 默认返回5条结果
    
    # 调用搜索函数
    results = search_rss_feeds(query, n_results)
    
    return results

@rss_bp.route('/', methods=['GET'])
def GetRss():
    return OutputRss()

@rss_bp.route('/all', methods=['GET'])
def GetAllRss():
    limit = request.args.get('limit', 20, type=int)
    date = request.args.get('date')
    sort_by_date = request.args.get('sort', 'desc').lower() == 'desc'  # 默认按时间从新到旧排序
    
    # 验证日期格式
    if date:
        try:
            # 验证日期格式是否为 YYYY-MM-DD
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Please use YYYY-MM-DD'}), 400
    
    # 获取RSSStorage实例，确保使用同一实例进行操作
    storage = RSSStorage()
    
    # 根据参数获取数据
    if date:
        # 按指定日期筛选
        feeds = storage.get_all_feeds(limit, date)
    else:
        # 获取所有数据按日期排序
        feeds = storage.get_all_feeds(limit)
    
    # 确保包含喜好信息
    # 获取所有喜好数据
    preferences = {pref["feed_id"]: pref for pref in storage.mongo_storage.get_all_preferences()}
    
    # 为每个结果添加喜好信息（确保结构完整）
    if 'ids' in feeds and feeds['ids'] and len(feeds['ids']) > 0 and isinstance(feeds['ids'][0], list):
        for i, doc_id in enumerate(feeds['ids'][0]):
            # 获取当前文档的喜好信息
            pref = preferences.get(doc_id, None)
            
            # 添加喜好信息到元数据
            if 'metadatas' in feeds and feeds['metadatas'] and i < len(feeds['metadatas'][0]):
                feeds['metadatas'][0][i]['user_preference'] = pref
        
        # 按发布日期排序（如果还没排序）
        if 'metadatas' in feeds and feeds['metadatas'] and len(feeds['metadatas'][0]) > 0:
            items = []
            for i in range(len(feeds['ids'][0])):
                item = {
                    'id': feeds['ids'][0][i],
                    'document': feeds['documents'][0][i] if 'documents' in feeds and feeds['documents'] else None,
                    'metadata': feeds['metadatas'][0][i] if 'metadatas' in feeds and feeds['metadatas'] else {}
                }
                items.append(item)
            
            # 按发布日期排序
            def sort_key(item):
                try:
                    metadata = item['metadata']
                    if 'pub_date' in metadata:
                        try:
                            return datetime.strptime(metadata['pub_date'], '%a, %d %b %Y %H:%M:%S %z')
                        except ValueError:
                            try:
                                return datetime.strptime(metadata['pub_date'], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                return datetime.strptime(metadata['pub_date'], '%Y-%m-%d')
                except (ValueError, TypeError):
                    pass
                return datetime(1970, 1, 1)  # 默认日期为早期时间
            
            # 从新到旧排序 (降序)
            items.sort(key=sort_key, reverse=True)
            
            # 重构结果
            feeds = {
                'ids': [[item['id'] for item in items]],
                'documents': [[item['document'] for item in items]] if 'documents' in feeds else None,
                'metadatas': [[item['metadata'] for item in items]] if 'metadatas' in feeds else None
            }
    
    return feeds

@rss_bp.route('/preference', methods=['POST'])
def StorePreference():
    data = request.get_json()
    # 验证参数
    if not data or 'feed_id' not in data or 'is_liked' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    feed_id = data['feed_id']
    is_liked = data['is_liked']
    reason = data.get('reason')
    
    # 存储喜好
    result = rss_storage.store_preference(feed_id, is_liked, reason)
    
    return jsonify(result)

@rss_bp.route('/dates', methods=['GET'])
def GetDatesWithData():
    """
    获取所有有RSS数据的日期列表
    """
    dates = rss_storage.get_dates_with_data()
    return jsonify(dates)

# 新增的RSS源管理相关API
@rss_bp.route('/sources', methods=['GET'])
def GetSources():
    """
    获取所有RSS订阅源
    """
    sources = rss_storage.mongo_storage.get_all_rss_sources()
    return jsonify(sources)

@rss_bp.route('/sources', methods=['POST'])
def AddSource():
    """
    添加新的RSS订阅源
    """
    data = request.get_json()
    # 验证参数
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing URL parameter'}), 400
    
    url = data['url']
    name = data.get('name', '')
    
    # 验证URL并尝试解析RSS
    try:
        # 尝试解析RSS，如果成功则添加源
        entries = ParseRss(url)
        if not entries:
            return jsonify({'error': 'Invalid RSS feed or no entries found'}), 400
        
        # 如果没有提供名称，使用第一个条目的标题作为源名称
        if not name and entries:
            name = f"Feed from {url}"
        
        # 存储RSS源
        result = rss_storage.mongo_storage.add_rss_source(url, name)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Failed to parse RSS: {str(e)}'}), 400

@rss_bp.route('/sources/<source_id>', methods=['DELETE'])
def DeleteSource(source_id):
    """
    删除RSS订阅源
    """
    try:
        result = rss_storage.mongo_storage.delete_rss_source(source_id)
        if result:
            return jsonify({'success': True, 'message': 'RSS source deleted'})
        else:
            return jsonify({'error': 'RSS source not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to delete RSS source: {str(e)}'}), 500
