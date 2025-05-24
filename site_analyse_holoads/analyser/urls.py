from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_video, name='upload'),
    #path('finaliser/', views.finaliser_enregistrement, name='finaliser_enregistrement'),
    #path('enregistrer-entreprise/', views.enregistrer_entreprise, name='enregistrer_entreprise'),
    


]
