from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required 

from .models import Document
from .forms import DocumentUploadForm

@login_required(login_url='/login')
def document_dashboard(request):
    """
    Renders the base layout with two empty divs that HTMX will fill.
    """
    return render(request, "document_manager/document_base.jinja")



@login_required(login_url='/login')
def document_list_panel(request):
    
    documents = documents = Document.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "document_manager/_document_list.jinja", {"documents": documents})

@login_required(login_url='/login')
def document_upload_panel(request):

    form = DocumentUploadForm()
    context = dict(
        form = form,
        has_errors = False,
        errors = [],
        is_success = False,
        success_message = ""
    )

    if request.method == "GET":
        return render(request, "document_manager/_document_upload.jinja", context=context)

    if request.method == "POST":
        response = render(request, "document_manager/_document_upload.jinja", context=context)
        response["HX-Trigger"] = "document-uploaded"

        return response
