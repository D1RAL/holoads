from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_video, name='upload'),
    path('emplacement/', views.emplacement, name='emplacement'),
    path('confirm-emplacement/', views.confirm_emplacement, name='confirm_emplacement'),
    path('facture/' ,views.facture, name='facture'),
]
