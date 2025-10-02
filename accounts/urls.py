from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.signin_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.signin_view, name='home'),
]