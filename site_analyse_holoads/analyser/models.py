# analyser/models.py
from django.db import models

class entreprises(models.Model):
    entreprise = models.CharField(max_length=200)
    email = models.EmailField()
    adresse = models.TextField(blank=True)
    domaine = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    video_path = models.CharField(max_length=500, blank=True)
    
    # Nouveau champ pour référencer l'enregistrement principal dans l'app videos
    video_id_reference = models.IntegerField(null=True, blank=True, verbose_name="ID de référence dans l'app videos")
    
    # Métadonnées pour traçabilité
    analyzed_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'analyse")
    
    class Meta:
        verbose_name = "Entreprise analysée"
        verbose_name_plural = "Entreprises analysées"
    
    def __str__(self):
        return self.entreprise