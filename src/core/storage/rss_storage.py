import chromadb
from chromadb.config import Settings
from datetime import datetime
from src.core.utils.config import getEnvVariable
from src.core.storage.mongodb_storage import MongoDBStorage

CHROMA_COLLECTION_NAME = getEnvVariable("CHROMA_COLLECTION_NAME")
CHROMA_HOST = getEnvVariable("CHROMA_HOST")
CHROMA_PORT = getEnvVariable("CHROMA_PORT")

class RSSStorage:
    def __init__(self, collection_name=CHROMA_COLLECTION_NAME, host=CHROMA_HOST, port=CHROMA_PORT):
        # 连接到Chroma服务
        self.client = chromadb.HttpClient(
            host=host,
            port=port
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "RSS feed storage"}
        )
        # 初始化MongoDB存储
        self.mongo_storage = MongoDBStorage()
    
    def store_feed(self, feed_data):
        """
        存储RSS feed数据
        feed_data: 包含title, link, description, pub_date等信息的字典
        """
        # 生成唯一ID
        doc_id = f"feed_{datetime.now().timestamp()}"
        
        # 准备存储数据
        documents = [f"{feed_data['title']}\n{feed_data['description']}"]
        metadatas = [{
            "title": feed_data['title'],
            "link": feed_data['link'],
            "pub_date": feed_data['pub_date'],
            "source": feed_data.get('source', '')
        }]
        
        # 存储到Chroma
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=[doc_id]
        )
        return doc_id
    
    def search_feeds(self, query, n_results=5):
        """
        搜索RSS feed
        query: 搜索关键词
        n_results: 返回结果数量
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return self._rank_results_by_preference(results)
    
    def get_all_feeds(self, limit=20):
        """
        获取所有RSS feed
        limit: 限制返回结果数量
        """
        # Chroma没有直接获取所有数据的方法，但我们可以使用空查询来获取
        results = self.collection.query(
            query_texts=[""],
            n_results=limit
        )
        return self._rank_results_by_preference(results)
    
    def _rank_results_by_preference(self, results):
        """
        根据用户喜好对结果进行排序
        """
        # 获取所有用户喜好
        preferences = {pref["feed_id"]: pref for pref in self.mongo_storage.get_all_preferences()}
        
        # 为结果添加喜好信息
        for i, doc_id in enumerate(results.get('ids', [[]])[0]):
            # 获取当前文档的喜好信息
            pref = preferences.get(doc_id, None)
            
            # 添加喜好信息到元数据
            if 'metadatas' in results and results['metadatas'] and i < len(results['metadatas'][0]):
                results['metadatas'][0][i]['user_preference'] = pref
        
        # 如果有多个结果，根据喜好进行排序
        if 'ids' in results and results['ids'] and len(results['ids'][0]) > 1:
            # 重新组织数据为可排序的格式
            items = []
            for i in range(len(results['ids'][0])):
                item = {
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i] if 'documents' in results and results['documents'] else None,
                    'metadata': results['metadatas'][0][i] if 'metadatas' in results and results['metadatas'] else {},
                    'distance': results['distances'][0][i] if 'distances' in results and results['distances'] else None
                }
                items.append(item)
            
            # 排序逻辑：喜欢的在前，不喜欢的在后，未标记的居中
            def sort_key(item):
                pref = item['metadata'].get('user_preference')
                if not pref:
                    return 1  # 未标记
                return 0 if pref['is_liked'] else 2  # 喜欢的为0，不喜欢的为2
            
            # 排序
            items.sort(key=sort_key)
            
            # 重构结果
            sorted_results = {
                'ids': [[item['id'] for item in items]],
                'documents': [[item['document'] for item in items]] if 'documents' in results else None,
                'metadatas': [[item['metadata'] for item in items]] if 'metadatas' in results else None,
                'distances': [[item['distance'] for item in items]] if 'distances' in results else None
            }
            
            return sorted_results
        
        return results
    
    def store_preference(self, feed_id, is_liked, reason=None):
        """
        存储用户对RSS的喜好
        """
        return self.mongo_storage.store_preference(feed_id, is_liked, reason) 