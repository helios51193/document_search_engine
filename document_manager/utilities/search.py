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
                    "snippet": c['text']
                }
                for c in top_chunks
            ],
            "matched_chunks": len(chunks),
        })

    results.sort(key=lambda r: r["best_score"], reverse=True)
    
    return results

def keyword_search(query: str, user_id:int):
    """
    Simple keyword search on chunk text.
    Returns list of dicts shaped like semantic hits.
    """
    if not query:
        return []
    
    qs = Chunk.objects.filter(
        document__owner_id=user_id,
        text__icontains=query,
    ).select_related("document")[:50]  # limit

    results = []
    for chunk in qs:
        results.append({
            "document_id": chunk.document.id,
            "document_title": chunk.document.title,
            "score": 1.0,  # full credit for keyword match
            "text": chunk.text,
        })

    return results


def hybrid_search(query, user_id, threshold=0.75):

    # 1. Get semantic hits
    semantic_hits = semantic_search(
        query=query,
        user_id=user_id,
        similarity_threshold=threshold,
    )

    # 2. Get keyword hits (raw, not aggregated)
    kw_hits = keyword_search(query, user_id)

    # Convert semantic results to same flat format
    flat_semantic = []
    for doc in semantic_hits:
        for c in doc["chunks"]:
            flat_semantic.append({
                "document_id": doc["document_id"],
                "document_title": doc["document_title"],
                "score": c["score"],
                "text": c["snippet"], 
            })
    
    # 3. Merge + dedupe by (document_id, text)
    combined = flat_semantic + kw_hits

    seen = set()
    merged = []
    for entry in combined:
        key = (entry["document_id"], entry["text"][:50])
        if key not in seen:
            seen.add(key)
            merged.append(entry)
    
    # 4. Reaggregate using existing logic
    grouped = {}
    for entry in merged:
        grouped.setdefault(entry["document_id"], []).append(entry)

    final = []
    for doc_id, chunks in grouped.items():
        chunks.sort(key=lambda c: c["score"], reverse=True)
        top = chunks[:3]
        final.append({
            "document_id": doc_id,
            "document_title": top[0]["document_title"],
            "best_score": round(top[0]["score"], 3),
            "chunks": [
                {
                    "score": c["score"],
                    "snippet": highlight_text(c["text"], query),
                }
                for c in top
            ],
            "matched_chunks": len(chunks),
        })
    

    final.sort(key=lambda r: r["best_score"], reverse=True)

    return final



