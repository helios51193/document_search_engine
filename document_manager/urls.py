from django.urls import path
from . import views

app_name = "document_manager"

urlpatterns = [
    # Partials
    path("panel/list/", views.document_list_panel, name="document_list_panel"),
    path("panel/upload/", views.document_upload_panel, name="document_upload_panel"),
    path("panel/search/input", views.document_search_input_panel, name="document_search_input_panel"),
    path("panel/search/result", views.document_search_result_panel, name="document_search_result_panel"),
    path("panel/progress/<int:document_id>", views.document_progress_panel, name="document_progress_panel"),
    
    # main pages/APIs
    path("dashboard/", views.document_dashboard, name="document_dashboard"),
    path("search/", views.document_search_page, name="document_search"),
    path("detail/<int:document_id>/", views.document_detail_page, name="document_detail"),
    path("delete/<int:document_id>/", views.delete_document, name="delete_document"),
    path("reindex/<int:document_id>/", views.reindex_document, name="reindex_document"),
]