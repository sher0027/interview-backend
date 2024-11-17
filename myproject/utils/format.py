import os
import tempfile
import ffmpeg
import pdfplumber
import requests
from io import BytesIO
from django.core.files.storage import default_storage

def convert_audio_to_wav(s3_audio_path, rid):
    file_extension = os.path.splitext(s3_audio_path)[1]

    with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_input_file:
        temp_input_file.write(default_storage.open(s3_audio_path).read())
        temp_input_path = temp_input_file.name

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_output_file:
        temp_output_path = temp_output_file.name

    ffmpeg.input(temp_input_path).output(temp_output_path, format='wav').run(overwrite_output=True)

    s3_directory = os.path.dirname(s3_audio_path)
    wav_filename = f"{os.path.splitext(os.path.basename(s3_audio_path))[0]}.wav"
    s3_wav_path = f"{s3_directory}/{wav_filename}"

    with open(temp_output_path, 'rb') as wav_file:
        s3_wav_path = default_storage.save(s3_wav_path, wav_file)
        s3_wav_url = default_storage.url(s3_wav_path)

    os.remove(temp_input_path)
    os.remove(temp_output_path)

    return s3_wav_url


def extract_text_from_pdf(s3_file_url):
    response = requests.get(s3_file_url)
    if response.status_code != 200:
        raise Exception("Failed to download PDF from S3")

    with pdfplumber.open(BytesIO(response.content)) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text()
    return full_text