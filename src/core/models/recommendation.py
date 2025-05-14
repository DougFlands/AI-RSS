import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime
from collections import defaultdict
import numpy as np
from src.core.storage.rss_storage import RSSStorage
from src.core.storage.mongodb_storage import MongoDBStorage
from src.core.utils.config import get_env_variable
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RSSRecommender:
    def __init__(self):
        """初始化RSS推荐系统"""
        self.rss_storage = RSSStorage()
        self.mongo_storage = MongoDBStorage()
        
        # 使用OpenAI的embedding函数
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # 用于存储用户的喜好模型
        self.user_preference_model = None
        
        # 初始化用户喜好模型
        self._initialize_user_preference_model()
    
    def _initialize_user_preference_model(self):
        """初始化用户喜好模型"""
        logger.info("初始化用户喜好模型")
        # 获取所有用户喜好记录
        preferences = self.mongo_storage.get_all_preferences()
        
        # 统计喜欢和不喜欢的数量
        liked_count = sum(1 for pref in preferences if pref.get('is_liked', False))
        disliked_count = sum(1 for pref in preferences if not pref.get('is_liked', True))
        
        logger.info(f"用户喜好统计: 喜欢 {liked_count} 条, 不喜欢 {disliked_count} 条")
        
        # 如果没有足够的喜好记录，暂不创建模型
        if liked_count + disliked_count < 5:
            logger.info("用户喜好记录不足，无法创建有效的推荐模型")
            self.user_preference_model = None
            return
        
        # 创建用户喜好模型
        self._train_user_preference_model(preferences)
    
    def _train_user_preference_model(self, preferences):
        """
        训练用户喜好模型
        
        Args:
            preferences: 用户喜好记录列表
        """
        if not preferences:
            self.user_preference_model = None
            return
        
        # 获取已标记喜好的feed ID
        feed_ids = [pref['feed_id'] for pref in preferences]
        
        # 获取这些feed的内容
        feeds = []
        for feed_id in feed_ids:
            feed_result = self.rss_storage.collection.get(ids=[feed_id])
            if feed_result and feed_result.get('documents') and feed_result.get('metadatas'):
                for i, doc in enumerate(feed_result.get('documents')):
                    feeds.append({
                        'id': feed_id,
                        'document': doc,
                        'metadata': feed_result.get('metadatas')[i]
                    })
        
        if not feeds:
            logger.warning("无法获取已标记喜好的feed内容")
            self.user_preference_model = None
            return
        
        # 创建用户喜好向量
        liked_docs = []
        disliked_docs = []
        
        for feed in feeds:
            pref = next((p for p in preferences if p['feed_id'] == feed['id']), None)
            if pref:
                if pref.get('is_liked', False):
                    liked_docs.append(feed['document'])
                else:
                    disliked_docs.append(feed['document'])
        
        # 计算喜欢文档的平均向量
        if liked_docs:
            liked_embeddings = self.embedding_function(liked_docs)
            liked_centroid = np.mean(liked_embeddings, axis=0).tolist()  # 转换为Python列表
        else:
            liked_centroid = None
        
        # 计算不喜欢文档的平均向量
        if disliked_docs:
            disliked_embeddings = self.embedding_function(disliked_docs)
            disliked_centroid = np.mean(disliked_embeddings, axis=0).tolist()  # 转换为Python列表
        else:
            disliked_centroid = None
        
        # 存储用户喜好模型
        self.user_preference_model = {
            'liked_centroid': liked_centroid,
            'disliked_centroid': disliked_centroid,
            'liked_count': len(liked_docs),
            'disliked_count': len(disliked_docs)
        }
        
        logger.info(f"用户喜好模型训练完成: 喜欢 {len(liked_docs)} 条, 不喜欢 {len(disliked_docs)} 条")
    
    def _compute_preference_score(self, feed_embedding):
        """
        计算feed与用户喜好的相似度分数
        
        Args:
            feed_embedding: feed的嵌入向量
            
        Returns:
            preference_score: 喜好分数，值越小表示越符合用户喜好
        """
        if not self.user_preference_model:
            return 0.5  # 如果没有用户喜好模型，返回中性分数
        
        liked_centroid = self.user_preference_model.get('liked_centroid')
        disliked_centroid = self.user_preference_model.get('disliked_centroid')
        
        if liked_centroid is None and disliked_centroid is None:
            return 0.5
        
        # 确保feed_embedding是numpy数组，以便计算
        if not isinstance(feed_embedding, np.ndarray):
            feed_embedding = np.array(feed_embedding)
        
        # 计算与喜欢中心的余弦相似度
        if liked_centroid is not None:
            # 转换为numpy数组
            liked_centroid_array = np.array(liked_centroid)
            # 计算余弦相似度
            liked_similarity = np.dot(feed_embedding, liked_centroid_array) / (
                np.linalg.norm(feed_embedding) * np.linalg.norm(liked_centroid_array))
            # 确保返回Python原生float
            liked_similarity = float(liked_similarity)
        else:
            liked_similarity = 0.0
        
        # 计算与不喜欢中心的余弦相似度
        if disliked_centroid is not None:
            # 转换为numpy数组
            disliked_centroid_array = np.array(disliked_centroid)
            disliked_similarity = np.dot(feed_embedding, disliked_centroid_array) / (
                np.linalg.norm(feed_embedding) * np.linalg.norm(disliked_centroid_array))
            # 确保返回Python原生float
            disliked_similarity = float(disliked_similarity)
        else:
            disliked_similarity = 0.0
        
        # 综合评分: 与喜欢中心的相似度越高、与不喜欢中心的相似度越低，分数越低（越好）
        if liked_centroid is not None and disliked_centroid is not None:
            # 平衡两个相似度的影响
            preference_score = 1.0 - liked_similarity + disliked_similarity
        elif liked_centroid is not None:
            preference_score = 1.0 - liked_similarity
        else:
            preference_score = disliked_similarity
        
        # 确保分数在合理范围内并返回Python原生float
        return float(max(0.0, min(1.0, preference_score)))
    
    def recommend_rss_feeds(self, limit=20, date=None, source_id=None):
        """
        推荐RSS feed
        
        Args:
            limit: 返回结果数量
            date: 可选，按日期过滤，格式为YYYY-MM-DD
            source_id: 可选，按订阅源URL筛选 (注意：虽然参数名是source_id，但实际值是source_url)
            
        Returns:
            推荐的RSS feed列表，按喜好分数排序（分数越小越符合用户喜好）
        """
        # 获取所有feed
        results = self.rss_storage.get_all_feeds(limit=1000, date=date)
        
        # 如果结果为空，返回原始结果
        if not results or 'ids' not in results or not results['ids'] or not results['ids'][0]:
            logger.warning("没有找到任何RSS feed")
            return results
        
        # 确保有用户喜好模型
        if not self.user_preference_model:
            self._initialize_user_preference_model()
        
        # 获取所有用户喜好
        preferences = {pref["feed_id"]: pref for pref in self.mongo_storage.get_all_preferences()}
        
        # 处理结果
        items = []
        for i, doc_id in enumerate(results['ids'][0]):
            # 获取当前文档
            document = results['documents'][0][i] if 'documents' in results and results['documents'] else ""
            metadata = results['metadatas'][0][i] if 'metadatas' in results and results['metadatas'] else {}
            
            # 如果已经有用户对该feed的明确喜好，直接使用
            explicit_preference = preferences.get(doc_id)
            if explicit_preference:
                preference_score = 0.0 if explicit_preference.get('is_liked') else 1.0
            else:
                # 计算文档的嵌入向量
                if document:
                    embedding = self.embedding_function([document])[0]
                    # 确保embedding是Python原生类型
                    embedding = np.array(embedding).tolist() if isinstance(embedding, np.ndarray) else embedding
                    # 计算用户喜好分数
                    preference_score = self._compute_preference_score(embedding)
                else:
                    preference_score = 0.5  # 如果没有文档内容，使用中性分数
            
            # 添加源URL过滤 (注意source_id参数实际包含的是URL)
            if source_id and metadata.get('source') != source_id:
                continue
            
            # 记录分数和元数据 (确保是Python原生类型)
            metadata['preference_score'] = float(preference_score)
            metadata['preference_order'] = int(preference_score * 100)  # 转换为0-100的整数分数
            
            # 添加到结果列表
            items.append({
                'id': doc_id,
                'document': document,
                'metadata': metadata,
                'preference_score': float(preference_score)  # 用于排序，确保是Python原生float
            })
        
        # 按喜好分数排序（分数越小越好）
        items.sort(key=lambda x: x['preference_score'])
        
        # 限制结果数量
        items = items[:limit]
        
        # 重构结果
        recommended_results = {
            'ids': [[item['id'] for item in items]],
            'documents': [[item['document'] for item in items]],
            'metadatas': [[item['metadata'] for item in items]]
        }
        
        return recommended_results
    
    def refresh_user_preference_model(self):
        """刷新用户喜好模型"""
        self._initialize_user_preference_model()
        return {"status": "success", "message": "用户喜好模型已刷新"}

# 确保所有numpy数组都转换为Python列表，解决JSON序列化问题
def convert_numpy_to_python_types(obj):
    """
    递归地将NumPy类型转换为Python原生类型
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.number):
        return obj.item()
    elif isinstance(obj, dict):
        return {k: convert_numpy_to_python_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_python_types(item) for item in obj]
    return obj

# 创建单例实例
recommender = RSSRecommender()

def get_rss_recommendations(limit=20, date=None, source_id=None):
    """获取RSS推荐"""
    # 获取推荐结果并确保所有NumPy类型都转换为Python原生类型
    results = recommender.recommend_rss_feeds(limit, date, source_id)
    return convert_numpy_to_python_types(results)

def refresh_recommendation_model():
    """刷新推荐模型"""
    return recommender.refresh_user_preference_model() 