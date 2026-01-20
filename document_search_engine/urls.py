"""
URL configuration for document_search_engine project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
def root_redirect(request):
    return redirect('auth_manager:auth_login')


urlpatterns = [
    path("", root_redirect),
    path('admin/', include('auth_manager.urls')),
    path('documents/',include('document_manager.urls', namespace="documents")),
    path('cadmin/', admin.site.urls),
]
