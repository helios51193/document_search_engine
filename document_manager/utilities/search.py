from qdrant_client.http import models as rest
from .embeddings import get_embedding
from document_manager.qdrant.qdrant_client import search_vectors
from document_manager.models import Chunk

def semantic_search(query:str, user_id:int, top_k: int = 10):

    query = query.strip()
    if not query:
        return []

    # Embed the query
    embedding = get_embedding(query)


    # Create filter
    query_filter = rest.Filter(
        must=[
            rest.FieldCondition(
                key="owner_id",
                match=rest.MatchValue(value=user_id),
            )
        ]
    )
    
    # Query Qdrant
    hits = search_vectors(
        query_embedding=embedding,
        top_k=top_k,
        filter_payload=query_filter,
    )

    # Map results to db chunks
    results = []
    for hit in hits:
        payload = hit["payload"]
        chunk_id = payload.get("chunk_id")
        try:
            chunk = Chunk.objects.select_related("document").get(id=chunk_id)
        except Chunk.DoesNotExist:
            print("chunk does not exist")
            continue
        
        results.append({
            "document_id": chunk.document.id,
            "document_title": chunk.document.title,
            "snippet": chunk.text[:400],
            "score": round(hit["score"], 4),
        })
    
    return results





