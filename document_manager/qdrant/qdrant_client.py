import traceback
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
import os
from django.conf import settings
import numpy as np


def qdrant_client() -> QdrantClient:
    if settings.QDRANT_API_KEY:
        return QdrantClient(url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}", api_key=settings.QDRANT_API_KEY)
    return QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


def ensure_collection():
    client = qdrant_client()
    existing_collection_names = [c.name for c in client.get_collections().collections]
    if settings.CHUNKS_COLLECTION_NAME not in existing_collection_names:
        client.recreate_collection(
            collection_name=settings.CHUNKS_COLLECTION_NAME,
            vectors_config=rest.VectorParams(size=settings.VECTOR_SIZE, distance=rest.Distance.COSINE),
        )
    
    if settings.DOCUMENT_COLLECTION_NAME not in existing_collection_names:
        client.recreate_collection(
            collection_name=settings.DOCUMENT_COLLECTION_NAME,
            vectors_config=rest.VectorParams(size=settings.VECTOR_SIZE, distance=rest.Distance.COSINE),
        )

def upsert_document_vector(doc_id:int,doc_title:str, mean_vec:np.ndarray):

    try:
        client = qdrant_client()
        # id can be chunk_id or str(document_id) + ":" + str(chunk_id)
        client.upsert(
            collection_name="documents",
            points=[
                rest.PointStruct(
                    id=doc_id,  # reuse doc PK for stable mapping
                    vector=mean_vec,
                    payload={"title": doc_title},
                )
            ]
        )
        return doc_id
    except Exception as e:
        print(f"{traceback.format_exc()}")
        return -1

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
            collection_name=settings.CHUNKS_COLLECTION_NAME,
            points=[
                rest.PointStruct(id=point_id, vector=embedding, payload=payload)
            ]
        )
        return point_id
    except Exception as e:
        print(f"{traceback.format_exc()}")
        return -1
        

def search_vectors(query_embedding: list, top_k=10, filter_payload=None):
    
    client:QdrantClient = qdrant_client()

    search_result = client.search(
        collection_name=settings.CHUNKS_COLLECTION_NAME,
        query_vector=query_embedding,
        limit=top_k,
        query_filter=filter_payload,  # Qdrant filter object, optional
        with_payload=True,
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
        collection_name=settings.CHUNKS_COLLECTION_NAME,
        query_filter=rest.Filter(must=[rest.FieldCondition(key="document_id", match=rest.MatchValue(value=document_id))])
    )

def delete_document_vectors(document_id:int):

    client = qdrant_client()

    selector = rest.FilterSelector(
        filter=rest.Filter(
            must=[
                rest.FieldCondition(
                    key="document_id",
                    match=rest.MatchValue(value=document_id),
                )
            ]
        )
    )

    client.delete(
        collection_name=settings.CHUNKS_COLLECTION_NAME,
        points_selector=selector,
    )

def get_similar_documents(doc_vector:any, limit:int=5):

    client = qdrant_client()

    results = client.search(
        collection_name="documents",
        query_vector=doc_vector,
        limit=limit + 1,  # include itself
    )

    return results

def fetch_chunk_vectors_for_doc(client, collection_name, doc_id):
    vectors = []
    next_offset = None

    while True:
        scroll_res = client.scroll(
            collection_name=collection_name,
            scroll_filter=rest.Filter(
                must=[
                    rest.FieldCondition(
                        key="document_id",
                        match=rest.MatchValue(value=doc_id)
                    )
                ]
            ),
            with_payload=False,
            with_vectors=True,
            limit=100,
            offset=next_offset,
        )

        points, next_offset, _ = scroll_res

        for p in points:
            if p.vector:
                vectors.append(p.vector)

        if next_offset is None:
            break

    return vectors
