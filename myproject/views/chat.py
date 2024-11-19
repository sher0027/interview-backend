import openai
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from myproject import settings
from myproject.utils.openai import get_openai_response
from myproject.repositories.record import RecordRepository
from myproject.repositories.user import UserRepository

openai.api_key = settings.OPENAI_API_KEY

class ChatView(APIView):
    parser_classes = [JSONParser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.record_repo = RecordRepository()
        self.user_repo = UserRepository()

    def post(self, request, version, *args, **kwargs):
        """
        Handle POST requests to generate interview responses.
        """
        rid = request.data.get("rid")
        company_info = request.data.get("companyInfo")

        if not rid or not company_info:
            return JsonResponse({"error": "Missing record ID or company information"}, status=400)

        try:
            uid = str(request.user.id)
            resume_info = self.user_repo.get_user(uid, version)
            if not resume_info:
                return JsonResponse({"error": "Resume not found for the user."}, status=404)

            records = self.record_repo.get_all_records(rid)
            if not records:
                return JsonResponse({"error": "No records found for the given record ID"}, status=404)

            chat_history = []
            seq_to_update = None
            for record in records:
                chat_history.append({"role": "user", "content": record['transcript']})
                if 'reply' in record and record['reply']:
                    chat_history.append({"role": "assistant", "content": record['reply']})
                else:
                    seq_to_update = record['seq']

            response_text = self._generate_interview_response(chat_history, resume_info, company_info)

            self.record_repo.update_reply(rid, seq_to_update, response_text)

            return JsonResponse({"response": response_text}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def _generate_interview_response(self, chat_history, resume_info, company_info):
        """
        Generate an interview response using OpenAI's GPT model.
        """
        company_name = company_info.get("name")
        role_name = company_info.get("role")
        job_description = company_info.get("description")

        system_message = (
            f"You are an interviewer from {company_name}.\n"
            f"A candidate is interviewing for the position of {role_name}.\n"
            f"Job Description: {job_description}\n"
            f"Resume: {resume_info}\n"
            "Please ask relevant interview questions based on the candidate's resume and responses.\n"
            "Begin with a general question such as 'Tell me about yourself', then proceed with questions one by one."
        )

        response = get_openai_response(
            model="gpt-3.5-turbo",
            system_message=system_message,
            user_messages=chat_history,
            max_tokens=100
        )
        return response['choices'][0]['message']['content']
