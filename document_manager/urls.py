from django.urls import path
from . import views

app_name = "document_manager"

urlpatterns = [
    path("dashboard/", views.document_dashboard, name="document_dashboard"),
    path("panel/list/", views.document_list_panel, name="document_list_panel"),
    path("panel/upload/", views.document_upload_panel, name="document_upload_panel"),
]