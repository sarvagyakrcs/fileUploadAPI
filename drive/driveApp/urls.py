# api/urls.py
from django.urls import path
from .views import FileListCreateView, FileRetrieveUpdateDestroyView

urlpatterns = [
    path('files/', FileListCreateView.as_view(), name='file-list-create'),
    path('files/<str:pk>/', FileRetrieveUpdateDestroyView.as_view(), name='file-detail'),
]
