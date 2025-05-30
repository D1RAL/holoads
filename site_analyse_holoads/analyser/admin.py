from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import entreprises, Commune, Emplacement

admin.site.register(entreprises)
admin.site.register(Commune)
admin.site.register(Emplacement)

