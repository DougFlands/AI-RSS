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
        返回: 新存储项目的ID或None（如果重复）
        """
        # 检查是否已经存在相同的feed（通过link或title+source判断）
        existing_feeds = self.collection.get(
            where={
                "$or": [
                    {"link": feed_data['link']}, 
                    {"$and": [
                        {"title": feed_data['title']},
                        {"source": feed_data.get('source', '')}
                    ]}
                ]
            }
        )
        
        # 如果找到匹配的结果，不再添加
        if existing_feeds and 'ids' in existing_feeds and existing_feeds['ids']:
            # 已经存在，不添加
            return None
        
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
    
    def get_all_feeds(self, limit=20, date=None):
        """
        获取所有RSS feed
        limit: 限制返回结果数量
        date: 可选，按日期过滤，格式为 YYYY-MM-DD
        """
        # 获取所有数据
        results = self.collection.get()
        
        # 如果结果为空或格式不符合预期，返回空结果
        if not results or 'ids' not in results or not results['ids']:
            return {'ids': [[]], 'documents': [[]], 'metadatas': [[]]}
        
        # 如果指定了日期，进行过滤
        if date:
            filtered_ids = []
            filtered_documents = []
            filtered_metadatas = []
            
            for i, metadata in enumerate(results.get('metadatas', [])):
                if 'pub_date' in metadata:
                    try:
                        # 尝试多种日期格式
                        try:
                            pub_date = datetime.strptime(metadata['pub_date'], '%a, %d %b %Y %H:%M:%S %z')
                        except ValueError:
                            try:
                                pub_date = datetime.strptime(metadata['pub_date'], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                pub_date = datetime.strptime(metadata['pub_date'], '%Y-%m-%d')
                        
                        if pub_date.strftime('%Y-%m-%d') == date:
                            filtered_ids.append(results['ids'][i])
                            filtered_documents.append(results['documents'][i])
                            filtered_metadatas.append(metadata)
                    except (ValueError, TypeError):
                        continue
            
            results = {
                'ids': [filtered_ids],
                'documents': [filtered_documents],
                'metadatas': [filtered_metadatas]
            }
        
        # 为结果添加喜好信息，但不排序
        preferences = {pref["feed_id"]: pref for pref in self.mongo_storage.get_all_preferences()}
        
        # 确保数据结构正确
        if 'ids' in results and results['ids'] and len(results['ids']) > 0:
            if isinstance(results['ids'][0], list):
                # 添加用户偏好信息
                for i, doc_id in enumerate(results['ids'][0]):
                    pref = preferences.get(doc_id, None)
                    if 'metadatas' in results and results['metadatas'] and i < len(results['metadatas'][0]):
                        results['metadatas'][0][i]['user_preference'] = pref
                        
                # 按日期排序（从新到旧）
                if 'metadatas' in results and results['metadatas'] and len(results['metadatas'][0]) > 0:
                    items = []
                    for i in range(len(results['ids'][0])):
                        item = {
                            'id': results['ids'][0][i],
                            'document': results['documents'][0][i] if 'documents' in results and results['documents'] else None,
                            'metadata': results['metadatas'][0][i] if 'metadatas' in results and results['metadatas'] else {}
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
                    
                    # 按日期从新到旧排序
                    items.sort(key=sort_key, reverse=True)
                    
                    # 限制结果数量
                    items = items[:limit]
                    
                    # 重构结果
                    results = {
                        'ids': [[item['id'] for item in items]],
                        'documents': [[item['document'] for item in items]] if 'documents' in results else None,
                        'metadatas': [[item['metadata'] for item in items]] if 'metadatas' in results else None
                    }
            else:
                # 数据是平面结构，需要转为嵌套结构
                results['ids'] = [results['ids']]
                if 'documents' in results and results['documents']:
                    results['documents'] = [results['documents']]
                if 'metadatas' in results and results['metadatas']:
                    results['metadatas'] = [results['metadatas']]
        
        return results
    
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
    
    def get_dates_with_data(self):
        """
        获取所有有RSS数据的日期列表
        返回格式: [{"date": "2024-03-20", "count": 10}, ...]
        """
        # 获取所有数据
        results = self.collection.get()
        
        # 统计每个日期的数据量
        date_counts = {}
        for metadata in results.get('metadatas', []):
            if 'pub_date' in metadata:
                try:
                    # 解析日期
                    pub_date = datetime.strptime(metadata['pub_date'], '%a, %d %b %Y %H:%M:%S %z')
                    date_str = pub_date.strftime('%Y-%m-%d')
                    
                    # 更新计数
                    date_counts[date_str] = date_counts.get(date_str, 0) + 1
                except (ValueError, TypeError):
                    continue
        
        # 转换为列表格式并按日期排序
        date_list = [{"date": date, "count": count} 
                    for date, count in date_counts.items()]
        date_list.sort(key=lambda x: x['date'], reverse=True)
        
        return date_list 