from pymongo import MongoClient
from bson import ObjectId
from src.core.utils.config import getEnvVariable
from datetime import datetime

class MongoDBStorage:
    def __init__(self, collection_name="user_preferences"):
        # 从环境变量获取MongoDB连接信息
        mongo_uri = getEnvVariable("MONGODB_URI") or "mongodb://192.168.2.4:47017/"
        db_name = getEnvVariable("MONGODB_DB_NAME") or "rss_app"
        
        # 连接到MongoDB
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        # RSS源存储集合
        self.rss_sources = self.db["rss_sources"]
    
    def _convert_objectid(self, data):
        """将MongoDB文档中的ObjectId转换为字符串"""
        if isinstance(data, dict):
            return {k: self._convert_objectid(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_objectid(item) for item in data]
        elif isinstance(data, ObjectId):
            return str(data)
        return data
    
    def store_preference(self, feed_id, is_liked, reason=None):
        """
        存储用户对RSS的喜好
        feed_id: RSS条目ID
        is_liked: 是否喜欢
        reason: 不喜欢的原因
        """
        data = {
            "feed_id": feed_id,
            "is_liked": is_liked,
            "reason": reason if not is_liked else None
        }
        
        # 更新已有记录或插入新记录
        self.collection.update_one(
            {"feed_id": feed_id},
            {"$set": data},
            upsert=True
        )
        return data
    
    def get_preference(self, feed_id):
        """
        获取用户对特定RSS的喜好
        """
        result = self.collection.find_one({"feed_id": feed_id})
        return self._convert_objectid(result) if result else None
    
    def get_all_preferences(self):
        """
        获取所有用户喜好
        """
        results = list(self.collection.find())
        return self._convert_objectid(results)
    
    def get_disliked_reasons(self):
        """
        获取所有不喜欢的原因
        """
        results = list(self.collection.find({"is_liked": False, "reason": {"$ne": None}}))
        return self._convert_objectid(results)
    
    # 添加RSS源管理相关方法
    def add_rss_source(self, url, name=""):
        """
        添加新的RSS源
        url: RSS源URL
        name: RSS源名称，可选
        """
        now = datetime.now()
        data = {
            "url": url,
            "name": name,
            "created_at": now,
            "updated_at": now
        }
        
        # 检查是否已存在相同URL的源
        existing = self.rss_sources.find_one({"url": url})
        if existing:
            return self._convert_objectid(existing)
        
        # 插入新记录
        result = self.rss_sources.insert_one(data)
        data["_id"] = result.inserted_id
        
        return self._convert_objectid(data)
    
    def get_all_rss_sources(self):
        """
        获取所有RSS源
        """
        results = list(self.rss_sources.find().sort("created_at", -1))
        return self._convert_objectid(results)
    
    def delete_rss_source(self, source_id):
        """
        删除RSS源
        source_id: RSS源ID
        """
        try:
            source_id = ObjectId(source_id)
            result = self.rss_sources.delete_one({"_id": source_id})
            return result.deleted_count > 0
        except:
            return False 