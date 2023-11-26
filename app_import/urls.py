from django.urls import path
from . import views # can have others views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload_file', views.upload_file, name='upload_file'),
    path('download_invoice/<str:filename>/', views.download_file, name='download_file'),

]


















