import openai
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from myproject import settings
from myproject.views import RecordView, ResumeView  

openai.api_key = settings.OPENAI_API_KEY 

class ChatView(APIView):
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        rid = request.data.get("rid")
        company_info = request.data.get("companyInfo")

        if not rid or not company_info:
            return JsonResponse({"error": "Missing record ID or company information"}, status=400)

        try:
            resume_view = ResumeView()
            resume_response = resume_view.get(request)
            if resume_response.status_code != 200:
                return resume_response 

            resume_info = resume_response
            
            record_view = RecordView()
            records_response = record_view.get(request, rid)
            if records_response.status_code != 200:
                return records_response  

            chat_history = []
            for item in records_response.get('records', []):
                chat_history.append({"role": "user", "content": item['transcript']})
                if 'reply' in item and item['reply']:  
                    chat_history.append({"role": "assistant", "content": item['reply']})

            response_text = self.generate_interview_response(chat_history, resume_info, company_info)
            self.save_reply(rid, response_text)

            return JsonResponse({"response": response_text}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def generate_interview_response(self, chat_history, resume_info, company_info):
        company_name = company_info.get("name")
        role_name = company_info.get("role")
        job_description = company_info.get("description")

        messages = [
            {
                "role": "system",
                "content": (
                    f"You are an interviewer from {company_name}.\n"
                    f"A candidate is interviewing for the position of {role_name}.\n"
                    f"Job Description: {job_description}\n"
                    f"Resume: {resume_info}\n"
                    "Please ask relevant interview questions based on the candidate's resume and responses.\n"
                    "Begin with a general question such as 'Tell me about yourself', then proceed with questions one by one."
                )
            },
            *chat_history  
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100
        )
        return response['choices'][0]['message']['content']

    def save_reply(self, rid, reply_text):
        record_view = RecordView()
        return record_view.update_reply(rid, reply_text) 
