# videos/models.py
from django.db import models
import os

class Video(models.Model):
    entreprise = models.CharField(max_length=200, verbose_name="Nom de l'entreprise")
    email = models.EmailField(verbose_name="Email de contact")
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    domaine = models.CharField(max_length=100, blank=True, verbose_name="Domaine d'activité")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    
    # Informations sur le fichier vidéo
    video_file = models.CharField(max_length=500, verbose_name="Chemin du fichier vidéo")
    original_filename = models.CharField(max_length=255, verbose_name="Nom original du fichier")
    file_size = models.BigIntegerField(verbose_name="Taille du fichier (bytes)")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    is_active = models.BooleanField(default=True, verbose_name="Vidéo active")
    
    class Meta:
        verbose_name = "Vidéo"
        verbose_name_plural = "Vidéos"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.entreprise} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def file_size_mb(self):
        """Retourne la taille du fichier en MB"""
        return round(self.file_size / (1024 * 1024), 2)
    
    def get_video_path(self):
        """Retourne le chemin complet vers la vidéo"""
        from django.conf import settings
        return os.path.join(settings.MEDIA_ROOT, self.video_file)
    
    def is_video(self):
        """Vérifie si le fichier est une vidéo basé sur l'extension"""
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
        _, ext = os.path.splitext(self.original_filename.lower())
        return ext in video_extensions
    
    def get_file_extension(self):
        """Retourne l'extension du fichier"""
        _, ext = os.path.splitext(self.original_filename)
        return ext.lower()
    
    @property
    def file_exists(self):
        """Vérifie si le fichier existe sur le disque"""
        return os.path.exists(self.get_video_path())