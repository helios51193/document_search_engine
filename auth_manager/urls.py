from django.urls import path
from . import views

urlpatterns = [path('login', views.login, name="auth_login"),
               path('logout', views.logout, name="auth_logout"),
               path('signup', views.logout, name="auth_signup"),]