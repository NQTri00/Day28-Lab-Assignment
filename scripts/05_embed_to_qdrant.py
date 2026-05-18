import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os
from dotenv import load_dotenv

load_dotenv()

EMBED_URL = os.environ.get("EMBED_NGROK_URL", "http://localhost:8002")
qdrant = QdrantClient(host="localhost", port=6333)

# Tạo collection
try:
    qdrant.recreate_collection(
        collection_name="documents",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
except Exception as e:
    print(f"Error recreating collection (maybe Qdrant is not running): {e}")

def embed_and_store(records: list[dict]):
    # Gọi Kaggle embedding service
    try:
        response = requests.post(f"{EMBED_URL}/embed", json={"texts": [r["text"] for r in records]}, headers={"ngrok-skip-browser-warning": "true"})
        embeddings = response.json()["embeddings"]
    except Exception as e:
        print(f"Failed to get embeddings. Check EMBED_NGROK_URL. Error: {e}")
        return

    points = [
        PointStruct(id=i, vector=emb, payload=rec)
        for i, (emb, rec) in enumerate(zip(embeddings, records))
    ]
    qdrant.upsert(collection_name="documents", points=points)
    print(f"Integration 5 OK: {len(points)} vectors stored in Qdrant")

if __name__ == "__main__":
    # Test với sample data
    embed_and_store([
        {"id": "doc_001", "text": "AI platform integration test"},
        {"id": "doc_002", "text": "Kafka to Airflow pipeline"},
    ])
