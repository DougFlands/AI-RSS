from flask import Blueprint, request, jsonify
from src.core.models.rss import OutputRss, search_rss_feeds, get_all_rss_feeds, ParseRss
from src.core.storage.rss_storage import RSSStorage
from datetime import datetime
from bson.objectid import ObjectId

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
    preference = request.args.get('preference')  # 添加喜好状态筛选参数：liked/disliked/unmarked/recommended/all
    source_id = request.args.get('source_id')  # 添加订阅源筛选参数
    
    # 验证日期格式
    if date:
        try:
            # 验证日期格式是否为 YYYY-MM-DD
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Please use YYYY-MM-DD'}), 400
    
    # 如果提供了source_id，先获取对应的URL
    source_url = None
    # 获取RSSStorage实例，确保使用同一实例进行操作
    storage = RSSStorage()
    
    if source_id:
        try:
            # 获取RSS源信息
            source = storage.mongo_storage.rss_sources.find_one({"_id": ObjectId(source_id)})
            if source:
                source_url = source.get("url")
            else:
                # 如果找不到对应的source_id，返回空结果
                return jsonify({'ids': [[]], 'documents': [[]], 'metadatas': [[]]}), 200
        except Exception as e:
            # 如果ID格式不正确或其他错误，返回错误信息
            return jsonify({'error': f'Invalid source_id: {str(e)}'}), 400
    print(source_url)
    # 如果请求是推荐模式，使用推荐算法
    if preference == 'recommended':
        try:
            # 导入推荐模块
            from src.core.models.recommendation import get_rss_recommendations
            
            # 使用推荐系统获取排序后的结果
            feeds = get_rss_recommendations(limit=limit, date=date, source_id=source_url)
            return feeds
        except ImportError:
            # 如果导入失败，继续使用默认排序
            pass
    
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
                    'metadata': feeds['metadatas'][0][i] if 'metadatas' in feeds and feeds['metadatas'] else {}
                }
                items.append(item)
            
            # 按发布日期排序
            def sort_key(item):
                try:
                    metadata = item['metadata']
                    if 'published' in metadata:
                        try:
                            return datetime.strptime(metadata['published'], '%a, %d %b %Y %H:%M:%S %z')
                        except ValueError:
                            try:
                                return datetime.strptime(metadata['published'], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                return datetime.strptime(metadata['published'], '%Y-%m-%d')
                except (ValueError, TypeError):
                    pass
                return datetime(1970, 1, 1)  # 默认日期为早期时间
            
            # 从新到旧排序 (降序)
            items.sort(key=sort_key, reverse=True)
            # 根据喜好状态筛选
            if preference:
                filtered_items = []
                for item in items:
                    pref = item['metadata'].get('user_preference')
                    
                    if preference == 'liked' and pref and pref.get('is_liked'):
                        filtered_items.append(item)
                    elif preference == 'disliked' and pref and not pref.get('is_liked'):
                        filtered_items.append(item)
                    elif preference == 'unmarked' and not pref:
                        filtered_items.append(item)
                    elif preference == 'all':
                        filtered_items.append(item)
                
                items = filtered_items

            # 根据订阅源筛选
            if source_url:
                items = [item for item in items if item['metadata'].get('source') == source_url]
            
            # 重构结果
            feeds = {
                'ids': [feeds['ids'][0]] if 'ids' in feeds else [[]],
                'documents': [feeds['documents'][0]] if 'documents' in feeds else [[]],
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

@rss_bp.route('/sources/<source_id>', methods=['PUT'])
def UpdateSource(source_id):
    """
    修改RSS订阅源
    """
    data = request.get_json()
    # 验证参数
    if not data:
        return jsonify({'error': 'Missing update parameters'}), 400
    
    # 可以更新的字段
    url = data.get('url')
    name = data.get('name')
    
    # 至少需要一个更新字段
    if not url and not name:
        return jsonify({'error': 'At least one field (url or name) is required for update'}), 400
    try:
        # 如果提供了新的URL，验证URL是否有效
        if url:
            try:
                # 尝试解析RSS，验证URL有效性
                entries = ParseRss(url)
                if not entries:
                    return jsonify({'error': 'Invalid RSS feed or no entries found'}), 400
            except Exception as e:
                return jsonify({'error': f'Failed to parse RSS: {str(e)}'}), 400
        
        # 更新RSS源
        result = rss_storage.mongo_storage.update_rss_source(source_id, url, name)
        if result:
            return jsonify({'success': True, 'message': 'RSS source updated', 'data': result})
        else:
            return jsonify({'error': 'RSS source not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to update RSS source: {str(e)}'}), 500
