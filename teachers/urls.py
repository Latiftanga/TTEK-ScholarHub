from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.teacher_list, name='list'),
    path('create/', views.teacher_create, name='create'),
    path('<int:pk>/', views.teacher_detail, name='detail'),
    path('<int:pk>/edit/', views.teacher_edit, name='edit'),
    path('<int:pk>/delete/', views.teacher_delete, name='delete'),
    path('bulk-upload/', views.teacher_bulk_upload, name='bulk_upload'),
    path('download-template/', views.download_template, name='download_template'),
]