import os
import tempfile
import requests
import openai
from myproject.utils.dynamoDB import get_dynamodb_table
from myproject.utils.format import convert_audio_to_wav
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from myproject.repositories.record import RecordRepository  
from datetime import datetime

openai.api_key = settings.OPENAI_API_KEY 

class AudioUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        self.record_repo = RecordRepository()  

    def post(self, request, *args, **kwargs):
        """
        Handle audio upload, transcription, and database storage.
        """
        audio_file = request.FILES.get('file')
        rid = request.data.get('rid')
        uid = str(request.user.id)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        if not audio_file or not rid:
            return JsonResponse({"error": "No audio file or record ID provided"}, status=400)

        try:
            audio_path = default_storage.save(f"user_{uid}/record_{rid}/{timestamp}_{audio_file.name}", audio_file)
            print(f"Successfully uploaded audio to: {audio_path}")

            wav_s3_url = convert_audio_to_wav(audio_path, rid)
            transcript = self._transcribe_audio(wav_s3_url)

            seq = self.record_repo.get_next_sequence(rid)  
            self.record_repo.save_record(rid, seq, transcript, wav_s3_url)

            default_storage.delete(audio_path)

            return JsonResponse({"transcript": transcript, "s3_url": wav_s3_url}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def _transcribe_audio(self, wav_s3_url):
        """
        Transcribe audio file to text using OpenAI's Whisper model.
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav_file:
            temp_wav_file.write(requests.get(wav_s3_url).content)
            temp_wav_path = temp_wav_file.name

        try:
            with open(temp_wav_path, 'rb') as audio_file:
                response = openai.Audio.transcribe("whisper-1", audio_file)
            return response.get('text', '')
        finally:
            os.remove(temp_wav_path)
