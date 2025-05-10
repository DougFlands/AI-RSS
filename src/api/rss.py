from flask import Blueprint, request, jsonify
from src.core.models.rss import OutputRss, search_rss_feeds, get_all_rss_feeds
from src.core.storage.rss_storage import RSSStorage

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
    return get_all_rss_feeds(limit)

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
