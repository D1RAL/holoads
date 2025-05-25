from django.urls import path
from . import views

app_name = 'videos'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:video_id>/', views.video_detail, name='video_detail'),
    path('<int:video_id>/download/', views.download_video, name='download_video'),
    path('<int:video_id>/stream/', views.stream_video, name='stream_video'),
]

