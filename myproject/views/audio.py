import os
from pydub import AudioSegment
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
import openai
from myproject import settings

openai.api_key = settings.OPENAI_API_KEY 

class AudioUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        audio_file = request.FILES.get('file')
        if not audio_file:
            return JsonResponse({"error": "No file provided"}, status=400)
        
        try:
            audio_path = default_storage.save(f"audio/{audio_file.name}", audio_file)

            # Convert audio to WAV format using pydub
            audio_segment = AudioSegment.from_file(audio_path)
            wav_path = f"{settings.MEDIA_ROOT}/audio/{audio_file.name.split('.')[0]}.wav"
            audio_segment.export(wav_path, format="wav")

            # Transcribe audio using OpenAI's Whisper API
            transcript = self.transcribe_audio(wav_path)

            return JsonResponse({"transcript": transcript}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def transcribe_audio(self, audio_path):
        with open(audio_path, 'rb') as audio_file:
            response = openai.Audio.transcribe("whisper-1", audio_file)
        return response.get('text', '')
