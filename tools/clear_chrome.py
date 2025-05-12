import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import chromadb
from src.core.utils.config import getEnvVariable

CHROMA_COLLECTION_NAME = getEnvVariable("CHROMA_COLLECTION_NAME")
CHROMA_HOST = getEnvVariable("CHROMA_HOST")
CHROMA_PORT = getEnvVariable("CHROMA_PORT")

client = chromadb.HttpClient(
    host=CHROMA_HOST,
    port=CHROMA_PORT
)

client.delete_collection(CHROMA_COLLECTION_NAME)
print(f"Chroma集合已清空")
