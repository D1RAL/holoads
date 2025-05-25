from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import os
import whisper
import shutil
import time
import re
from .models import entreprises
from videos.models import Video  # Import du modèle Video de l'app videos

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOTS_CLES_PATH = os.path.join(BASE_DIR, 'mots_cles.txt')

def home(request):
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

def upload_video(request):
    result_message = ""
    mots_trouves = []
    form_data = {}
    analyse_terminee = False
    is_valid = False

    if request.method == 'POST' and request.FILES.get('video'):
        form_data['entreprise'] = request.POST.get('entreprise', '')
        form_data['email'] = request.POST.get('email', '')
        form_data['adresse'] = request.POST.get('adresse', '')
        form_data['domaine'] = request.POST.get('domaine', '')
        form_data['telephone'] = request.POST.get('telephone', '')
        
        video_file = request.FILES['video']
        
        # Sauvegarde temporaire
        fs = FileSystemStorage()
        filename = fs.save(video_file.name, video_file)
        video_path = fs.path(filename)

        try:
            # Transcription avec Whisper
            model = whisper.load_model("base")
            result = model.transcribe(video_path, language='fr', task='transcribe')
            transcription = result["text"]

            # DEBUG: Afficher la transcription (à supprimer en production)
            print(f"TRANSCRIPTION: {transcription}")

            # Sauvegarder la transcription
            output_dir = os.path.join(BASE_DIR, "IA_PYTHON")
            os.makedirs(output_dir, exist_ok=True)
            output_filename = os.path.splitext(video_file.name)[0] + "_transcription.txt"
            output_path = os.path.join(output_dir, output_filename)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"Entreprise: {form_data['entreprise']}\n")
                f.write(f"Email: {form_data['email']}\n")
                f.write("="*50 + "\n")
                f.write(transcription)

            # Charger les mots interdits
            with open(MOTS_CLES_PATH, "r", encoding="utf-8") as f:
                mots_cles = [mot.strip() for mot in f if mot.strip() and not mot.strip().startswith('#')]

            # DEBUG: Afficher les mots-clés (à supprimer en production)
            print(f"MOTS CLES: {mots_cles}")

            # Nouvelle méthode de détection
            mots_trouves = detecter_mots_interdits(transcription, mots_cles)

            # DEBUG: Afficher les mots trouvés (à supprimer en production)
            print(f"MOTS TROUVES: {mots_trouves}")

            if mots_trouves:
                is_valid = False
                result_message = (
                    "❌ Votre annonce n'a pas pu être validée car elle contient des mots ou expressions "
                    "qui ne sont pas conformes à nos règles. Veuillez téléverser une autre vidéo conforme à nos critères. "
                    "Les mots ou expressions non conformes que nous avons trouvés sont : "
                    + ", ".join(mots_trouves)
                )
                # Supprimer la vidéo temporaire en cas de refus
                os.remove(video_path)
                form_data = {}
            else:
                is_valid = True
                
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
                shutil.move(video_path, final_video_path)
                
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
                    
                    result_message = f"✅ Votre annonce a été validée et votre vidéo a été sauvegardée. Aucun mot interdit détecté."
                    form_data = {}  # Vider le formulaire après succès
                    
                except Exception as e:
                    # En cas d'erreur lors de la sauvegarde en base, supprimer le fichier
                    if os.path.exists(final_video_path):
                        os.remove(final_video_path)
                    raise e

        except Exception as e:
            # En cas d'erreur, supprimer le fichier temporaire
            if os.path.exists(video_path):
                os.remove(video_path)
            result_message = f"❌ Erreur lors de l'analyse : {str(e)}"
            is_valid = False

    analyse_terminee = True

    return render(request, 'analyser/upload.html', {
        'result_message': result_message,
        'mots_trouves': mots_trouves,
        'form_data': form_data,
        'is_valid': is_valid,
        'analyse_terminee': analyse_terminee
    })