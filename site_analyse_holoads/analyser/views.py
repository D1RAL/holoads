from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import os
import whisper
import shutil
import time
import re
import json
from .models import entreprises
from .models import Commune
from .models import Emplacement
from videos.models import Video  # Import du modèle Video de l'app videos

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOTS_CLES_PATH = os.path.join(BASE_DIR, 'mots_cles.txt')

def home(request):
    """Vue pour la page d'accueil"""
    return render(request, 'analyser/index.html')

def nettoyer_texte(texte):
    """Nettoie le texte en supprimant la ponctuation et en normalisant"""
    # Convertir en minuscules
    texte = texte.lower()
    # Supprimer la ponctuation et caractères spéciaux, garder seulement lettres, chiffres et espaces
    texte = re.sub(r'[^\w\s]', ' ', texte)
    # Remplacer plusieurs espaces par un seul
    texte = re.sub(r'\s+', ' ', texte)
    return texte.strip()

def detecter_mots_interdits(transcription, mots_cles):
    """Détecte les mots interdits dans la transcription avec une approche plus robuste"""
    
    # Nettoyer la transcription
    transcription_nettoyee = nettoyer_texte(transcription)
    mots_trouves = []
    
    for mot_cle in mots_cles:
        mot_cle_nettoye = nettoyer_texte(mot_cle)
        
        # Méthode 1: Recherche exacte du mot/expression complète
        if mot_cle_nettoye in transcription_nettoyee:
            mots_trouves.append(mot_cle.strip())
            continue
            
        # Méthode 2: Recherche avec regex pour les mots complets
        pattern = r'\b' + re.escape(mot_cle_nettoye) + r'\b'
        if re.search(pattern, transcription_nettoyee):
            mots_trouves.append(mot_cle.strip())
            continue
        
        # Méthode 3: Recherche des mots individuels si l'expression contient plusieurs mots
        # Par exemple, si mot_cle = "le sexe", on cherche aussi juste "sexe"
        mots_individuels = mot_cle_nettoye.split()
        if len(mots_individuels) > 1:
            for mot_individuel in mots_individuels:
                # Ignorer les mots très courts comme "le", "la", "de", etc.
                if len(mot_individuel) > 2 and mot_individuel not in ['les', 'des', 'une', 'avec', 'pour', 'sur', 'dans']:
                    pattern_individuel = r'\b' + re.escape(mot_individuel) + r'\b'
                    if re.search(pattern_individuel, transcription_nettoyee):
                        mots_trouves.append(mot_cle.strip())
                        break  # Sortir de la boucle des mots individuels
            if mots_trouves and mots_trouves[-1] == mot_cle.strip():
                continue  # Mot déjà trouvé, passer au suivant
            
        # Méthode 4: Recherche de variantes proches (pluriels, etc.)
        if len(mot_cle_nettoye) > 3:
            pattern_variant = r'\b' + re.escape(mot_cle_nettoye) + r's?\b'
            if re.search(pattern_variant, transcription_nettoyee):
                mots_trouves.append(mot_cle.strip())
                continue
                
        # Méthode 5: Pour les expressions, essayer aussi sans les articles
        if len(mots_individuels) > 1:
            # Supprimer les articles courants
            mots_sans_articles = [mot for mot in mots_individuels if mot not in ['le', 'la', 'les', 'un', 'une', 'des', 'du', 'de']]
            if mots_sans_articles:
                expression_sans_articles = ' '.join(mots_sans_articles)
                if expression_sans_articles != mot_cle_nettoye:  # Éviter la duplication
                    pattern_sans_articles = r'\b' + re.escape(expression_sans_articles) + r'\b'
                    if re.search(pattern_sans_articles, transcription_nettoyee):
                        mots_trouves.append(mot_cle.strip())
                        continue
    
    return list(set(mots_trouves))  # Supprimer les doublons

def valider_formulaire(form_data):
    """Valide les données du formulaire"""
    erreurs = []
    
    # Validation du nom d'entreprise
    if not form_data.get('entreprise', '').strip():
        erreurs.append("Le nom de l'entreprise est requis")
    elif len(form_data['entreprise']) > 200:
        erreurs.append("Le nom de l'entreprise ne peut pas dépasser 200 caractères")
    
    # Validation de l'email
    email = form_data.get('email', '').strip()
    if not email:
        erreurs.append("L'adresse e-mail est requise")
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        erreurs.append("L'adresse e-mail n'est pas valide")
    
    # Validation de l'adresse
    if not form_data.get('adresse', '').strip():
        erreurs.append("L'adresse de l'entreprise est requise")
    elif len(form_data['adresse']) > 500:
        erreurs.append("L'adresse ne peut pas dépasser 500 caractères")
    
    # Validation du domaine
    if not form_data.get('domaine', '').strip():
        erreurs.append("Le domaine d'activité est requis")
    elif len(form_data['domaine']) > 200:
        erreurs.append("Le domaine d'activité ne peut pas dépasser 200 caractères")
    
    # Validation du téléphone
    telephone = form_data.get('telephone', '').strip()
    if not telephone:
        erreurs.append("Le numéro de téléphone est requis")
    elif not re.match(r'^[\d\s+\-\(\)\.]{8,20}$', telephone):
        erreurs.append("Le numéro de téléphone n'est pas valide")
    
    return erreurs

def upload_video(request):
    """Vue principale pour l'upload et l'analyse de vidéo"""
    result_message = ""
    mots_trouves = []
    form_data = {}
    analyse_terminee = False
    is_valid = False
    erreurs_validation = []

    # Initialiser form_data avec les valeurs POST pour persistance
    if request.method == 'POST':
        form_data = {
            'entreprise': request.POST.get('entreprise', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'adresse': request.POST.get('adresse', '').strip(),
            'domaine': request.POST.get('domaine', '').strip(),
            'telephone': request.POST.get('telephone', '').strip(),
        }

    # Traiter la soumission du formulaire (avec ou sans action spécifique)
    if request.method == 'POST' and request.FILES.get('video'):
        # Validation du formulaire
        erreurs_validation = valider_formulaire(form_data)
        
        # Validation du formulaire
        erreurs_validation = valider_formulaire(form_data)
        
        if erreurs_validation:
            result_message = "❌ Erreurs de validation : " + "; ".join(erreurs_validation)
            analyse_terminee = True
        else:
            video_file = request.FILES['video']
            
            # Validation du type de fichier
            allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
            file_extension = os.path.splitext(video_file.name)[1].lower()
            
            if file_extension not in allowed_extensions:
                result_message = "❌ Format de fichier non supporté. Formats acceptés : MP4, AVI, MOV, MKV, WMV, FLV"
                analyse_terminee = True
            elif video_file.size > 100 * 1024 * 1024:  # 100 MB
                result_message = "❌ Le fichier est trop volumineux (maximum 100 MB)"
                analyse_terminee = True
            else:
                # Procéder à l'analyse
                print(f"Début de l'analyse pour {video_file.name}")
                is_valid, result_message, mots_trouves = traiter_video(video_file, form_data)
                analyse_terminee = True
                
                # Si l'analyse échoue, vider form_data seulement si c'est une erreur technique
                if not is_valid and not mots_trouves:
                    form_data = {}

    # Gérer les cas où il n'y a pas de fichier vidéo mais une action
    elif request.method == 'POST' and not request.FILES.get('video'):
        result_message = "❌ Veuillez sélectionner une vidéo"
        analyse_terminee = True

    context = {
        'result_message': result_message,
        'mots_trouves': mots_trouves,
        'form_data': form_data,
        'is_valid': is_valid,
        'analyse_terminee': analyse_terminee,
        'erreurs_validation': erreurs_validation
    }

    return render(request, 'analyser/upload.html', context)

def traiter_video(video_file, form_data):
    """Traite la vidéo : transcription et analyse"""
    try:
        # Sauvegarde temporaire
        fs = FileSystemStorage()
        filename = fs.save(video_file.name, video_file)
        video_path = fs.path(filename)

        # Vérifier que le fichier a bien été sauvegardé
        if not os.path.exists(video_path):
            return False, "❌ Erreur lors de la sauvegarde du fichier", []

        try:
            # Transcription avec Whisper
            print(f"Début de la transcription pour : {video_file.name}")
            model = whisper.load_model("base")
            result = model.transcribe(video_path, language='fr', task='transcribe')
            transcription = result["text"]

            # Vérifier que la transcription n'est pas vide
            if not transcription.strip():
                os.remove(video_path)
                return False, "❌ Impossible d'extraire l'audio de la vidéo ou audio vide", []

            # DEBUG: Afficher la transcription (à supprimer en production)
            print(f"TRANSCRIPTION: {transcription}")

            # Sauvegarder la transcription
            sauvegarder_transcription(video_file.name, form_data, transcription)

            # Charger les mots interdits
            mots_cles = charger_mots_interdits()

            # DEBUG: Afficher les mots-clés (à supprimer en production)
            print(f"MOTS CLES: {mots_cles}")

            # Détecter les mots interdits
            mots_trouves = detecter_mots_interdits(transcription, mots_cles)

            # DEBUG: Afficher les mots trouvés (à supprimer en production)
            print(f"MOTS TROUVES: {mots_trouves}")

            if mots_trouves:
                # Supprimer la vidéo temporaire en cas de refus
                os.remove(video_path)
                result_message = (
                    "❌ Votre annonce n'a pas pu être validée car elle contient des mots ou expressions "
                    "qui ne sont pas conformes à nos règles. Veuillez téléverser une autre vidéo conforme à nos critères. "
                    "Les mots ou expressions non conformes détectés sont : "
                    + ", ".join(f'"{mot}"' for mot in mots_trouves)
                )
                return False, result_message, mots_trouves
            else:
                # Vidéo validée, sauvegarder en base
                success, message = sauvegarder_video_validee(video_file, video_path, form_data)
                return success, message, []

        except Exception as e:
            # En cas d'erreur, supprimer le fichier temporaire
            if os.path.exists(video_path):
                os.remove(video_path)
            print(f"Erreur lors de l'analyse : {str(e)}")
            return False, f"❌ Erreur lors de l'analyse : {str(e)}", []

    except Exception as e:
        print(f"Erreur générale : {str(e)}")
        return False, f"❌ Erreur générale : {str(e)}", []

def charger_mots_interdits():
    """Charge la liste des mots interdits depuis le fichier"""
    try:
        if not os.path.exists(MOTS_CLES_PATH):
            print(f"ATTENTION: Fichier mots_cles.txt non trouvé à {MOTS_CLES_PATH}")
            return []
            
        with open(MOTS_CLES_PATH, "r", encoding="utf-8") as f:
            mots_cles = [mot.strip() for mot in f if mot.strip() and not mot.strip().startswith('#')]
        
        return mots_cles
    except Exception as e:
        print(f"Erreur lors du chargement des mots interdits : {str(e)}")
        return []

def sauvegarder_transcription(filename, form_data, transcription):
    """Sauvegarde la transcription dans un fichier"""
    try:
        output_dir = os.path.join(BASE_DIR, "IA_PYTHON")
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.splitext(filename)[0] + "_transcription.txt"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"Entreprise: {form_data['entreprise']}\n")
            f.write(f"Email: {form_data['email']}\n")
            f.write(f"Adresse: {form_data['adresse']}\n")
            f.write(f"Domaine: {form_data['domaine']}\n")
            f.write(f"Téléphone: {form_data['telephone']}\n")
            f.write("="*50 + "\n")
            f.write("TRANSCRIPTION:\n")
            f.write(transcription)
            
        print(f"Transcription sauvegardée : {output_path}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la transcription : {str(e)}")

def sauvegarder_video_validee(video_file, temp_video_path, form_data):
    """Sauvegarde la vidéo validée et les données en base"""
    try:
        # Créer un nom unique pour la vidéo
        timestamp = str(int(time.time()))
        entreprise_clean = "".join(c for c in form_data['entreprise'] if c.isalnum() or c in (' ', '-', '_')).strip()
        entreprise_clean = entreprise_clean.replace(' ', '_')[:50]
        
        # Extension du fichier original
        file_extension = os.path.splitext(video_file.name)[1]
        new_filename = f"{entreprise_clean}_{timestamp}{file_extension}"
        
        # Créer le dossier media/videos s'il n'existe pas
        media_videos_dir = os.path.join(BASE_DIR, 'media', 'videos')
        os.makedirs(media_videos_dir, exist_ok=True)
        
        # Chemin final pour la vidéo
        final_video_path = os.path.join(media_videos_dir, new_filename)
        
        # Déplacer la vidéo du stockage temporaire vers media/videos/
        shutil.move(temp_video_path, final_video_path)
        
        try:
            # Enregistrer dans l'app videos (table principale)
            video_instance = Video.objects.create(
                entreprise=form_data['entreprise'],
                email=form_data['email'],
                adresse=form_data['adresse'],
                domaine=form_data['domaine'],
                telephone=form_data['telephone'],
                video_file=f"videos/{new_filename}",
                original_filename=video_file.name,
                file_size=video_file.size if hasattr(video_file, 'size') else os.path.getsize(final_video_path)
            )
            
            # Optionnel: Enregistrer aussi dans l'app analyser pour traçabilité
            entreprises.objects.create(
                entreprise=form_data['entreprise'],
                email=form_data['email'],
                adresse=form_data['adresse'],
                domaine=form_data['domaine'],
                telephone=form_data['telephone'],
                video_path=f"videos/{new_filename}",
                video_id_reference=video_instance.id  # Référence vers l'enregistrement principal
            )
            
            success_message = (
                f"✅ Félicitations ! Votre annonce a été validée avec succès. "
                f"Aucun contenu non conforme détecté. Votre vidéo a été sauvegardée "
                f"et vous êtes maintenant enregistré dans notre système. "
                f"Vous pouvez finaliser votre enregistrement pour choisir l'emplacement d'affichage."
            )
            
            print(f"Vidéo sauvegardée avec succès : {final_video_path}")
            print(f"Enregistrement en base réussi pour l'entreprise : {form_data['entreprise']}")
            
            return True, success_message
            
        except Exception as e:
            # En cas d'erreur lors de la sauvegarde en base, supprimer le fichier
            if os.path.exists(final_video_path):
                os.remove(final_video_path)
            print(f"Erreur lors de la sauvegarde en base : {str(e)}")
            return False, f"❌ Erreur lors de l'enregistrement en base : {str(e)}"

    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la vidéo : {str(e)}")
        return False, f"❌ Erreur lors de la sauvegarde : {str(e)}"

@csrf_exempt
def check_progress(request):
    """API endpoint pour vérifier le progrès de l'analyse (optionnel)"""
    if request.method == 'GET':
        # Cette vue pourrait être utilisée pour un suivi en temps réel
        # Pour l'instant, on retourne un statut simple
        return JsonResponse({
            'status': 'processing',
            'progress': 50,
            'message': 'Analyse en cours...'
        })
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

def emplacement(request):
    """Vue pour la page de sélection d'emplacement (à implémenter)"""
    # Cette vue doit être implémentée selon vos besoins
    # Elle pourrait afficher une carte ou une liste d'emplacements disponibles
    return render(request, 'analyser/emplacement.html')




def emplacement_view(request):
    # Récupérer toutes les communes disponibles
    communes = Commune.objects.all()
    
    # Préparer les données pour JavaScript
    communes_data = []
    for commune in communes:
        communes_data.append({
            'id': commune.id,
            'name': commune.name,
            'description': commune.description,
            'price': commune.price,
            'lat': commune.latitude,
            'lng': commune.longitude,
            'color': commune.color
        })
    
    context = {
        'communes': communes_data
    }
    
    return render(request, 'emplacement.html', context)


@csrf_exempt
def confirm_emplacement(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        commune_id = data.get('commune_id')
        
        try:
            commune = Commune.objects.get(id=commune_id)
            
            # Créer ou mettre à jour l'emplacement
            emplacement, created = Emplacement.objects.get_or_create(
                user=request.user,
                defaults={'commune': commune, 'confirmed': True}
            )
            
            if not created:
                emplacement.commune = commune
                emplacement.confirmed = True
                emplacement.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Emplacement confirmé avec succès',
                'commune_name': commune.name
            })
            
        except Commune.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Commune non trouvée'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    })

def facture(request) : 
    return render(request,'analyser/facture.html')

