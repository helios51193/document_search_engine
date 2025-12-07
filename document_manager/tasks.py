from celery import shared_task
from django.db import transaction

from .models import Document
from .utilities.utils import extract_text_from_file

@shared_task
def process_document(document_id):
    doc = Document.objects.get(id=document_id)

    doc.status = "indexing"
    doc.save(update_fields=["status"])

    try:
        text = extract_text_from_file(doc.file.path)
        with transaction.atomic():
            doc.content_text = text
            doc.status = "ready"
            doc.save(update_fields=["content_text", "status"])
    
    except Exception as e:
        doc.status = "error"
        doc.metadata['error'] = str(e)
        doc.save(update_fields=["status"])
        raise