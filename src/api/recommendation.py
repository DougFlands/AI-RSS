from flask import Blueprint, request, jsonify
from src.core.models.recommendation import get_rss_recommendations, refresh_recommendation_model

# 创建蓝图
recommendation_bp = Blueprint("recommendation", __name__, url_prefix="/recommendation")

@recommendation_bp.route('/rss', methods=['GET'])
def recommend_rss():
    """
    获取推荐的RSS内容，根据用户喜好排序
    
    查询参数:
        limit: 限制返回结果数量，默认20
        date: 可选，按日期过滤，格式为YYYY-MM-DD
        source_id: 可选，按订阅源ID过滤
    
    返回:
        排序后的RSS feed列表，按喜好程度排序（喜好值越小表示越符合用户喜好）
    """
    # 获取查询参数
    limit = request.args.get('limit', 20, type=int)
    date = request.args.get('date')
    source_id = request.args.get('source_id')
    
    # 调用推荐函数
    results = get_rss_recommendations(limit=limit, date=date, source_id=source_id)
    
    return jsonify(results)

@recommendation_bp.route('/refresh', methods=['POST'])
def refresh_model():
    """
    刷新推荐模型
    
    用于在用户喜好发生大量变化后重新训练模型
    
    返回:
        刷新状态
    """
    result = refresh_recommendation_model()
    return jsonify(result) 