from django.db import models

class entreprises(models.Model):
    entreprise = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    adresse = models.TextField()
    domaine = models.CharField(max_length=255)
    telephone = models.CharField(max_length=50)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.entreprise
