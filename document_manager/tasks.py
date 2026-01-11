from django.conf import settings
from django.utils import timezone
import traceback
from celery import shared_task
from django.db import transaction
from .utilities.tokenizer import count_tokens

from document_manager.utilities.embeddings import get_embedding

from .models import Document, Chunk
from .utilities.utils import extract_text_from_file
from .utilities.chunking import chunk_text
from pprint import pprint
from .qdrant.qdrant_client  import ensure_collection, upsert_document_vector, upsert_vector
import numpy as np
import logging
logger = logging.getLogger(__name__)



def compute_mean_vector(embeddings):
    """Chunks = queryset or list of obj with embedding."""
    
    vectors = np.array(embeddings)
    mean_vec = np.mean(vectors, axis=0).tolist()
    return mean_vec



@shared_task
def process_document(document_id):


    logger.info(f"Chunking document {document_id}")
    doc = Document.objects.get(id=document_id)

    doc.status = "indexing"
    doc.embedding_model = settings.EMBEDDING_PROVIDER
    doc.save(update_fields=["status", "embedding_model"])

    try:
        # Extract
        text = extract_text_from_file(doc.file.path)
        with transaction.atomic():
            doc.content_text = text
            doc.save(update_fields=["content_text"])
        
        # Chunking
        chunks = chunk_text(text, max_chars=1200)
        chunk_objs = []
        for c in chunks:
            chunk_objs.append(Chunk.objects.create(document=doc, index=c['index'], text=c['text'], start_offset=c['start'], end_offset=c['end']))

        ensure_collection()
        total = len(chunk_objs)
        total_tokens = 0
        embeddings = []
        for idx,chunk in enumerate(chunk_objs):
            embedding = get_embedding(chunk.text)  # dispatches to OpenAI or Ollama
            total_tokens += count_tokens(chunk.text)
            payload = {
                "owner_id":doc.owner_id,
                "document_id": doc.id,
                "chunk_id": chunk.id,
                "title": doc.title,
            }
            pprint(payload)
            point_id = upsert_vector(chunk_id=chunk.id, embedding=embedding, payload=payload)
            chunk.vector_id = point_id
            chunk.save(update_fields=["vector_id"])
            embeddings.append(embedding)

            doc.progress = 40 + int((idx / total) * 50)
            doc.save(update_fields=["progress"])
        
        # after chunk embeddings stored:
        chunks = Chunk.objects.filter(document_id=doc.id)
        mean_vec = compute_mean_vector(embeddings)

        # store in qdrant
        res = upsert_document_vector(doc.id, doc.title, mean_vec)
        print(res)

        doc.status = "ready"
        doc.chunk_count = len(chunk_objs)
        doc.token_count = total_tokens
        doc.progress = 100
        doc.last_indexed_at = timezone.now()
        doc.save(update_fields=["status", "progress","last_indexed_at","chunk_count","token_count"])

        logger.info(f"Completed Chunking document {document_id}")
        # optional future: send event via webhook / redis pubsub
        return {"status":'ok', "timezone":timezone.now()}
    
    except Exception as e:
        logger.error(f"Error while chunking {e}", exc_info=True)
        doc.status = "error"
        doc.metadata['error'] = str(e)
        print(f"{traceback.format_exc()}")
        doc.save(update_fields=["status"])
        raise