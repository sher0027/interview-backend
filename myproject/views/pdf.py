import re
import json
from myproject.utils.format import extract_text_from_pdf
import openai
from myproject import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from myproject.repositories.user import UserRepository
from datetime import datetime

openai.api_key = settings.OPENAI_API_KEY 

class PDFUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = UserRepository()

    def post(self, request, *args, **kwargs):
        uid = str(request.user.id)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        pdf_file = request.FILES.get('file')
        if not pdf_file:
            return JsonResponse({"error": "No PDF file provided"}, status=400)

        try:
            pdf_path = default_storage.save(f"user_{uid}/resumes/{timestamp}_{pdf_file.name}", pdf_file)
            print(f"Successfully uploaded PDF to: {pdf_path}")
            if not pdf_path:
                return JsonResponse({"error": "Failed to save file to storage"}, status=500)

            s3_file_url = default_storage.url(pdf_path)
            if not s3_file_url:
                return JsonResponse({"error": "Failed to get file URL from storage"}, status=500)

            pdf_text = extract_text_from_pdf(s3_file_url)
            parsed_data = self._extract_resume_info(pdf_text)
            parsed_data['url'] = s3_file_url

            if 'error' not in parsed_data:
                self.repo.upload_resume(uid, parsed_data)

            return JsonResponse(parsed_data, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    def _extract_resume_info(self, text):
        messages = [
            {"role": "system", "content": "You are an AI assistant skilled in parsing resume information."},
            {"role": "user", "content": (
                f"Extract the following fields from the resume text:\n\n"
                f"{text}\n\n"
                "Return a JSON with these fields: name, email, phone, address, education(list of objects), workExperience(if any, list of objects), projects(if any, list of objects),skills."
                " Respond only with JSON data without additional text."
            )}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.2
        )

        response_content = response.choices[0].message['content'].strip()

        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                parsed_data = json.loads(json_str)
            except json.JSONDecodeError:
                return {"error": "Failed to parse the response as JSON. Response content: " + response_content}
        else:
            return {"error": "No valid JSON found in the response. Response content: " + response_content}

        return parsed_data
    
