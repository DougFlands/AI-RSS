import os
import sys
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import chromadb
from src.core.utils.config import get_env_variable

CHROMA_COLLECTION_NAME = get_env_variable("CHROMA_COLLECTION_NAME")
CHROMA_HOST = get_env_variable("CHROMA_HOST")
CHROMA_PORT = get_env_variable("CHROMA_PORT")

def search_all_data():
    """
    查询Chroma数据库中的所有数据
    返回: 所有存储在Chroma中的数据
    """
    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT
    )
    
    try:
        # 获取集合
        collection = client.get_collection(name=CHROMA_COLLECTION_NAME)
        
        # 获取所有数据
        results = collection.get()
        
        # 数据处理
        if results and 'ids' in results and results['ids']:
            # 创建结构化的结果
            structured_results = []
            
            for i in range(len(results['ids'])):
                item = {
                    'id': results['ids'][i],
                    'document': results['documents'][i] if 'documents' in results and i < len(results['documents']) else None,
                    'metadata': results['metadatas'][i] if 'metadatas' in results and i < len(results['metadatas']) else {}
                }
                structured_results.append(item)
            
            return structured_results
        else:
            print("集合中没有数据")
            return []
    
    except Exception as e:
        print(f"查询出错: {e}")
        return []

def print_formatted_results(results):
    """格式化打印结果"""
    if not results:
        print("没有找到数据")
        return
    
    print(f"共找到 {len(results)} 条数据:")
    print("=" * 80)
    
    for i, item in enumerate(results, 1):
        print(f"[{i}] ID: {item['id']}")
        
        if item['metadata']:
            print("  元数据:")
            for key, value in item['metadata'].items():
                # 对长文本进行截断显示
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"    {key}: {value}")
        
        if item['document']:
            # 对长文档进行截断显示
            doc = item['document']
            if len(doc) > 150:
                doc = doc[:150] + "..."
            print(f"  文档内容: {doc}")
        
        print("-" * 80)

if __name__ == "__main__":
    # 查询所有数据
    results = search_all_data()
    
    # 输出格式化结果
    print_formatted_results(results)
    
    # 是否需要导出为JSON
    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        output_file = "chroma_data_export.json"
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"数据已导出到: {output_file}")
