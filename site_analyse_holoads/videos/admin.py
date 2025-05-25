# videos/admin.py
from django.contrib import admin
from .models import Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'entreprise', 'email', 'domaine', 'file_size_mb_display', 'created_at', 'is_active')
    list_filter = ('domaine', 'is_active', 'created_at')
    search_fields = ('entreprise', 'email', 'domaine')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'file_size_mb_display')
    
    fieldsets = (
        ('Informations entreprise', {
            'fields': ('entreprise', 'email', 'adresse', 'domaine', 'telephone')
        }),
        ('Fichier vidéo', {
            'fields': ('video_file', 'original_filename', 'file_size', 'file_size_mb_display')
        }),
        ('Métadonnées', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_mb_display(self, obj):
        """Affiche la taille du fichier en MB"""
        return f"{obj.file_size_mb} MB"
    file_size_mb_display.short_description = "Taille (MB)"
    file_size_mb_display.admin_order_field = 'file_size'
    
    def get_queryset(self, request):
        """Optimise les requêtes"""
        return super().get_queryset(request).select_related()