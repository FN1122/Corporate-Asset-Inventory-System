"""
URL configuration for caims project.
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='registration/login.html'),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # App
    path('', account_views.dashboard, name='dashboard'),
]
