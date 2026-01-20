import traceback
from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required

from document_manager.utilities.search import explain_single_document, hybrid_search, similar_documents
from document_manager.utilities.services import reset_document_for_reindex 
from .tasks import process_document
from django.shortcuts import render, get_object_or_404
from .models import Document,SearchEvent
from .forms import DocumentUploadForm
from .qdrant.qdrant_client import delete_document_vectors
from django.db.models import Count, Avg, Max
import logging
logger = logging.getLogger(__name__)

@login_required(login_url='/admin/login')
def document_dashboard(request):
    """
    Renders the base layout with two empty divs that HTMX will fill.
    """
    return render(request, "document_manager/document_base.jinja")



@login_required(login_url='/admin/login')
def document_list_panel(request):
    
    documents = documents = Document.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "document_manager/_document_list.jinja", {"documents": documents})

@login_required(login_url='/admin/login')
def document_upload_panel(request):

    form = DocumentUploadForm()
    context = dict(
        form = form,
        has_errors = False,
        errors = [],
        is_success = False,
        success_message = ""
    )
    try:
        if request.method == "GET":
            return render(request, "document_manager/_document_upload.jinja", context=context)

        if request.method == "POST":
            
            form = DocumentUploadForm(request.POST, request.FILES)
            if form.is_valid():
                doc = form.save(commit=False)
                doc.owner = request.user
                doc.status = "pending"
                doc.save()

                # trigger async processing
                process_document.delay(doc.id)

                # Prepare the context
                context['is_success'] = True
                context['success_message'] = "File Uploaded Successfully"  
            else:
                context['has_errors'] = True
                context['errors'] = ["Some Error occured, check form values"]

            response = render(request, "document_manager/_document_upload.jinja", context=context)
            response["HX-Trigger"] = "document-uploaded"

            return response
    except Exception as e:
        print(f"{traceback.format_exc()}")
        context['has_errors'] = True
        context['is_success'] = False
        context['errors'] = ["Some Internal Error occured"]
        return render(request, "document_manager/_document_upload.jinja", context=context)


@login_required(login_url='/admin/login')
def document_search_input_panel(request):

    context = {}

    return render(request, "document_manager/_search_input_panel.jinja", context=context)


@login_required(login_url='/admin/login')
def document_search_result_panel(request):

    query = request.GET.get("q", "").strip()
    threshold = float(request.GET.get("threshold", 0.75))
    results = []
    if query:
        results = hybrid_search(
            query=query,
            user_id=request.user.id,
            threshold=threshold
        )
        top = results[0]["best_score"] if results else None
        SearchEvent.objects.create(
            user=request.user,
            query=query,
            threshold=threshold,
            result_count=len(results),
            top_score=top,
        )

    context = {
        "query":query,
        "results":results,
        "threshold":threshold
    }

    print(query)

    return render(request, "document_manager/_search_result_panel.jinja", context=context)

@login_required(login_url='/admin/login')
def document_search_page(request):

    context = {}

    return render(request, "document_manager/document_search_base.jinja", context=context)

@login_required(login_url='/admin/login')
def document_detail_page(request, document_id):

    context = {}
    document = None
    try:
        document = Document.objects.get(id=int(document_id), owner=request.user)
    except Document.DoesNotExist:
        pass

    context['document'] = document

    return render(request, "document_manager/document_detail.jinja", context=context)

@login_required(login_url='/admin/login')
def delete_document(request, document_id:int):

    if request.method != "POST":
        return HttpResponse(status=405)
    
    try:
        document = Document.objects.get(id=document_id, owner=request.user)
    except Exception as e:
        return HttpResponse(status=404)
    
    # Delete vectors from qdrant
    delete_document_vectors(document.id)

    #delete document
    document.delete()

    # Tell HTMX that something has changed
    response = HttpResponse("")
    response["HX-Trigger"] = "document-deleted"
    return response

@login_required(login_url='/admin/login')
def reindex_document(request, document_id):

    if request.method != "POST":
        return HttpResponse(status=405)
    
    try:
        document = Document.objects.get(id=document_id, owner=request.user)
    except Exception as e:
        return HttpResponse(status=404)
    
    reset_document_for_reindex(document)

    process_document.delay(document.id)

    response = HttpResponse("")
    response["HX-Trigger"] = "document-reindexed"
    return response

@login_required(login_url='/admin/login')
def document_progress_panel(request, document_id):

    document = get_object_or_404(
        Document,
        id=document_id,
        owner=request.user,
    )
    response = render(
        request,
        "document_manager/_document_progress.jinja",
        {"document": document},
    )

    # trigger to update the doc list and re-evaluate the button statuses
    if document.status == "ready" and request.headers.get("HX-Request"):
        response["HX-Trigger"] = "document-indexed"
    
    return response

@login_required(login_url='/admin/login')
def analytics_page(request):

    return render(request, "document_manager/document_search_analytics_base.jinja")


@login_required(login_url='/admin/login')
def analytics_summary_panel(request):
    total = SearchEvent.objects.count()
    unique = SearchEvent.objects.values("query").distinct().count()
    avg = SearchEvent.objects.aggregate(avg=Avg("result_count"))["avg"] or 0
    recent = SearchEvent.objects.order_by("-created_at").first()

    return render(
        request,
        "document_manager/_analytics_summary_panel.jinja",
        {
            "total": total,
            "unique": unique,
            "avg_results": avg,
            "recent": recent.query if recent else "—",
        }
    )

@login_required(login_url='/admin/login')
def analytics_table_panel(request):
    events = SearchEvent.objects.order_by("-created_at")[:50]
    return render(
        request,
        "document_manager/_analytics_table_panel.jinja",
        {"events": events}
    )

@login_required(login_url='/admin/login')
def similar_docs_panel(request, doc_id):
    related = similar_documents(doc_id)
    return render(
        request,
        "document_manager/_document_similar_document.jinja",
        {"related": related},
    )

@login_required(login_url='/admin/login')
def explain_result_panel(request, doc_id):

    query = request.GET.get("q", "")
    threshold = float(request.GET.get("threshold", 0.75))

    result = explain_single_document(
        document_id=doc_id,
        query=query,
        threshold=threshold,
        user_id=request.user.id,
    )

    return render(request, "document_manager/_explain_result_panel.jinja",
        {"explain": result},
    )