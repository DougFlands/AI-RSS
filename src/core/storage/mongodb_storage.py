from pymongo import MongoClient
from bson import ObjectId
from src.core.utils.config import get_env_variable
from datetime import datetime

class MongoDBStorage:
    def __init__(self, collection_name="user_preferences"):
        # 从环境变量获取MongoDB连接信息
        mongo_uri = get_env_variable("MONGODB_URI") 
        db_name = get_env_variable("MONGODB_DB_NAME")

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
    
    def update_rss_source(self, source_id, url=None, name=None):
        """
        更新RSS源信息
        source_id: RSS源ID
        url: 新的URL，可选
        name: 新的名称，可选
        返回: 更新后的RSS源数据或None（如果未找到）
        """
        try:
            source_id = ObjectId(source_id)
            
            # 构建更新数据
            update_data = {"updated_at": datetime.now()}
            if url:
                update_data["url"] = url
            if name:
                update_data["name"] = name
            
            # 更新记录
            result = self.rss_sources.update_one(
                {"_id": source_id},
                {"$set": update_data}
            )
            
            # 如果记录存在并已更新
            if result.matched_count > 0:
                # 获取更新后的数据
                updated_source = self.rss_sources.find_one({"_id": source_id})
                return self._convert_objectid(updated_source)
            return None
            
        except Exception as e:
            print(f"更新RSS源出错: {e}")
            return None
    
    def store_rss_url(self, url, name=None):
        """
        存储RSS URL
        url: RSS源的URL
        name: 可选，RSS源的名称
        返回: 添加成功返回True，已存在返回False
        """
        # 检查URL是否已存在
        existing = self.db.rss_urls.find_one({"url": url})
        if existing:
            return False
        
        # 存储新URL
        self.db.rss_urls.insert_one({
            "url": url,
            "name": name,
            "created_at": datetime.now()
        })
        return True
    
    def get_all_rss_urls(self):
        """
        获取所有存储的RSS URL
        返回: URL列表 [{"url": "http://...", "name": "源名称"}, ...]
        """
        urls = list(self.rss_sources.find().sort("created_at", -1))
        return urls
    
    def delete_rss_url(self, url):
        """
        删除RSS URL
        url: 要删除的RSS URL
        返回: 删除成功返回True，不存在返回False
        """
        result = self.db.rss_urls.delete_one({"url": url})
        return result.deleted_count > 0 