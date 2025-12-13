import traceback
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
import os
from django.conf import settings


QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)  # if using cloud


COLLECTION_NAME = "doc_chunks"

def qdrant_client() -> QdrantClient:
    if QDRANT_API_KEY:
        return QdrantClient(url=f"http://{QDRANT_HOST}:{QDRANT_PORT}", api_key=QDRANT_API_KEY)
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, check_compatibility=False)


def ensure_collection():
    client = qdrant_client()
    if COLLECTION_NAME not in [c.name for c in client.get_collections().collections]:
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=rest.VectorParams(size=settings.VECTOR_SIZE, distance=rest.Distance.COSINE),
        )

def upsert_vector(chunk_id: int, embedding: list, payload: dict):
    """
    Inserts a single vector into Qdrant and returns the Qdrant point id.
    We'll use an internal point id based on chunk_id (or let Qdrant generate one).
    """
    try:
        client = qdrant_client()
        # id can be chunk_id or str(document_id) + ":" + str(chunk_id)
        point_id = chunk_id
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                rest.PointStruct(id=point_id, vector=embedding, payload=payload)
            ]
        )
        return point_id
    except Exception as e:
        print(f"{traceback.format_exc()}")
        return -1
        

def search_vectors(query_embedding: list, top_k=10, filter_payload=None):
    client = qdrant_client()

    search_result = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding,
        limit=top_k,
        query_filter=filter_payload,  # Qdrant filter object, optional
    )

    # Map to a simple list
    results = []
    for hit in search_result:
        results.append({
            "id": hit.id,
            "score": hit.score,
            "payload": hit.payload,
        })
    return results

def delete_document_vectors(document_id: int):
    client = qdrant_client()
    # delete by payload filter
    client.delete(
        collection_name=COLLECTION_NAME,
        query_filter=rest.Filter(must=[rest.FieldCondition(key="document_id", match=rest.MatchValue(value=document_id))])
    )