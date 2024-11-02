import os
import tempfile
import ffmpeg
import requests
import openai
from myproject.utils import get_dynamodb_table
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from boto3.dynamodb.conditions import Key
from myproject import settings

openai.api_key = settings.OPENAI_API_KEY 

class AudioUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        self.records_table = get_dynamodb_table('records')

    def post(self, request, *args, **kwargs):
        audio_file = request.FILES.get('file')
        rid = request.data.get('rid') 
        if not audio_file or not rid:
            return JsonResponse({"error": "No audio file or record ID provided"}, status=400)

        try:
            audio_path = default_storage.save(f"{rid}/{audio_file.name}", audio_file)
            print("Successfully uploaded audio to S3!")
            
            wav_s3_url = self.convert_audio_to_wav(audio_path, rid)
            transcript = self.transcribe_audio(wav_s3_url)
            self.save_record(rid, transcript, wav_s3_url)

            default_storage.delete(audio_path)

            return JsonResponse({"transcript": transcript, "s3_url": wav_s3_url}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def convert_audio_to_wav(self, s3_audio_path, rid):
        file_extension = os.path.splitext(s3_audio_path)[1]

        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_input_file:
            temp_input_file.write(default_storage.open(s3_audio_path).read())
            temp_input_path = temp_input_file.name
    
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_output_file:
            temp_output_path = temp_output_file.name

        ffmpeg.input(temp_input_path).output(temp_output_path, format='wav').run(overwrite_output=True)

        wav_filename = f"{os.path.splitext(os.path.basename(s3_audio_path))[0]}.wav" 
        with open(temp_output_path, 'rb') as wav_file:
            s3_wav_path = default_storage.save(f"{rid}/{wav_filename}", wav_file)
            s3_wav_url = default_storage.url(s3_wav_path)

        os.remove(temp_input_path)
        os.remove(temp_output_path)

        return s3_wav_url
    
    def transcribe_audio(self, wav_s3_url):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav_file:
            temp_wav_file.write(requests.get(wav_s3_url).content)
            temp_wav_path = temp_wav_file.name

        with open(temp_wav_path, 'rb') as audio_file:
            response = openai.Audio.transcribe("whisper-1", audio_file)

        os.remove(temp_wav_path)

        return response.get('text', '')

    def save_record(self, rid, transcript, s3_url):
        table = get_dynamodb_table('records')

        response = table.query(
            KeyConditionExpression=Key('rid').eq(rid),
            ProjectionExpression="seq",
            ScanIndexForward=False, 
            Limit=1 
        )

        if 'Items' in response and response['Items']:
            last_seq = response['Items'][0]['seq']
            next_seq = last_seq + 1
        else:
            next_seq = 1 

        record_data = {
            'rid': rid,
            'seq': next_seq,
            'transcript': transcript,
            's3_url': s3_url
        }

        table.put_item(Item=record_data)
        print("Record saved to DB successfully with seq:", next_seq)
