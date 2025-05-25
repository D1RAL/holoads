# videos/views.py
from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, HttpResponse
from .models import Video
import os
import mimetypes

def index(request):
    videos = Video.objects.all().order_by('-created_at')  # Changé de Media à Video et de uploaded_at à created_at
    return render(request, 'videos/index.html', {'videos': videos})

def video_detail(request, video_id):
    video = get_object_or_404(Video, pk=video_id)  # Changé de Media à Video
    return render(request, 'videos/video_detail.html', {'video': video})

def download_video(request, video_id):
    video = get_object_or_404(Video, pk=video_id)  # Changé de Media à Video
    file_path = video.get_video_path()  # Utilise la méthode du modèle
    
    if os.path.exists(file_path):
        content_type, encoding = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{video.original_filename}"'  # Utilise le champ du modèle
        return response
    
    return HttpResponse("Le fichier n'existe pas")

def stream_video(request, video_id):
    video = get_object_or_404(Video, pk=video_id)  # Changé de Media à Video
    file_path = video.get_video_path()  # Utilise la méthode du modèle
    
    if os.path.exists(file_path):
        content_type, encoding = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'video/mp4'  # Par défaut pour les vidéos
        
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        return response
    
    return HttpResponse("Le fichier n'existe pas")