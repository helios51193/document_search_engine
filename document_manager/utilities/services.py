from document_manager.models import Document, Chunk
from document_manager.qdrant.qdrant_client import delete_document_vectors


def reset_document_for_reindex(document: Document):


    # Delete vectors from Qdrant
    delete_document_vectors(document.id)

    # Delete chunks from DB
    Chunk.objects.filter(document=document).delete()

    # Reset document fields
    document.status = "pending"
    document.progress = 0
    document.content_text = ""
    document.save(update_fields=["status", "content_text"])