from django.shortcuts import render
from django.core.files.storage import FileSystemStorage


def home(request):
    return render(request, 'analyser/index.html')

import os
import whisper
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage  # <- ajoute cette ligne
from .models import entreprises

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOTS_CLES_PATH = os.path.join(BASE_DIR, 'mots_cles.txt')

def upload_video(request):
    result_message = ""
    mots_trouves = []
    form_data = {}
    analyse_terminee = False
    is_valid = False
    video_path = None  # <- On initialise ici pour éviter l'erreur

    if request.method == 'POST' and request.FILES.get('video'):
        form_data['entreprise'] = request.POST.get('entreprise', '')
        form_data['email'] = request.POST.get('email', '')
        form_data['adresse'] = request.POST.get('adresse', '')
        form_data['domaine'] = request.POST.get('domaine', '')
        form_data['telephone'] = request.POST.get('telephone', '')
        video_file = request.FILES['video']
        fs = FileSystemStorage()
        filename = fs.save(video_file.name, video_file)
        video_path = fs.path(filename)  # <- cette variable est bien définie ici

        # Transcription avec Whisper
        model = whisper.load_model("base")
        result = model.transcribe(video_path, language='fr', task='transcribe')
        transcription = result["text"]

        # Sauvegarder la transcription
        output_dir = os.path.join(BASE_DIR, "IA PYTHON")
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.splitext(video_file.name)[0] + "_transcription.txt"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(transcription)

        # Vérifier les mots interdits
        with open(MOTS_CLES_PATH, "r", encoding="utf-8") as f:
            mots_cles = {mot.strip().lower() for mot in f if mot.strip()}

        mots_texte = {mot.strip('.,!?').lower() for mot in transcription.split()}
        mots_trouves = list(mots_cles.intersection(mots_texte))

        if mots_trouves:
            is_valid = False
            result_message = (
                "❌ Votre annonce n'a pas pu être validée car elle contient des mots ou expressions "
                "non conformes : " + ", ".join(mots_trouves)
            )
            form_data = {}
        else:
            is_valid = True
            result_message = "✅ Votre annonce a été validée."
            entreprises.objects.create(
                entreprise=form_data['entreprise'],
                email=form_data['email'],
                adresse=form_data['adresse'],
                domaine=form_data['domaine'],
                telephone=form_data['telephone']
            )

    # Ce bloc ne s’exécute que si video_path a été défini
    if video_path:
        if is_valid:
            accepted_dir = os.path.join(BASE_DIR, "pubs_acceptees")
            os.makedirs(accepted_dir, exist_ok=True)
            new_video_path = os.path.join(accepted_dir, os.path.basename(video_path))
            os.rename(video_path, new_video_path)
        else:
            os.remove(video_path)

    analyse_terminee = True

    return render(request, 'analyser/upload.html', {
        'result_message': result_message,
        'mots_trouves': mots_trouves,
        'form_data': form_data,
        'is_valid': is_valid,
        'analyse_terminee': analyse_terminee
    })
