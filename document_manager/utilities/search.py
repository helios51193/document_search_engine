from qdrant_client.http import models as rest
from collections import defaultdict
from document_manager.utilities.highlighting import highlight_text
from .embeddings import get_embedding
from document_manager.qdrant.qdrant_client import search_vectors
from document_manager.models import Chunk

def semantic_search(query:str, user_id:int, top_k: int = 20, max_chunks_per_doc=3, similarity_threshold=0.30):

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

    grouped = defaultdict(list)

    # Groups chunks by document
    for hit in hits:
        payload = hit["payload"]
        chunk = None
        score = hit['score']
        # Check for threshold
        if score < similarity_threshold:
            continue
            # discard weak chunks

        try:
            chunk = Chunk.objects.select_related("document").get(id=payload['chunk_id'])
        except Chunk.DoesNotExist:
            print(f"Chunk does not exist {payload}")
            continue
        grouped[payload["document_id"]].append({
            "score": hit["score"],
            "document_title": chunk.document.title,
            "text": chunk.text,
        })
    
    results = []

    # Build document level results
    for document_id, chunks in grouped.items():
        # sort chunks by score (desc)
        chunks.sort(key=lambda c: c["score"], reverse=True)

        top_chunks = chunks[:max_chunks_per_doc]

        results.append({
            "document_id": document_id,
            "document_title": top_chunks[0]["document_title"],
            "best_score": round(top_chunks[0]["score"], 3),
            "chunks": [
                {
                    "score": round(c["score"], 3),
                    "snippet": highlight_text(c["text"], query),
                }
                for c in top_chunks
            ],
            "matched_chunks": len(chunks),
        })

    results.sort(key=lambda r: r["best_score"], reverse=True)
    
    return results





