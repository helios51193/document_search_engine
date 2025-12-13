import traceback
from celery import shared_task
from django.db import transaction

from document_manager.embeddings import get_embedding

from .models import Document, Chunk
from .utilities.utils import extract_text_from_file
from .chunking import chunk_text
from pprint import pprint
from .qdrant.qdrant_client  import ensure_collection, upsert_vector
@shared_task
def process_document(document_id):
    doc = Document.objects.get(id=document_id)

    doc.status = "indexing"
    doc.save(update_fields=["status"])

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

        for chunk in chunk_objs:
            embedding = get_embedding(chunk.text)  # dispatches to OpenAI or Ollama
            payload = {
                "document_id": doc.id,
                "chunk_id": chunk.id,
                "title": doc.title,
            }
            pprint(payload)
            point_id = upsert_vector(chunk_id=chunk.id, embedding=embedding, payload=payload)
            chunk.vector_id = point_id
            chunk.save(update_fields=["vector_id"])
        
        doc.status = "ready"
        doc.save(update_fields=["status"])


        return {"status":'ok'}
    
    except Exception as e:
        doc.status = "error"
        doc.metadata['error'] = str(e)
        print(f"{traceback.format_exc()}")
        doc.save(update_fields=["status"])
        raise