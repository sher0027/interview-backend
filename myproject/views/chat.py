import openai
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
import os
from myproject import settings

openai.api_key = settings.OPENAI_API_KEY 

class ChatView(APIView):
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        user_message = request.data.get("message")
        if not user_message:
            return JsonResponse({"error": "No message provided"}, status=400)

        try:
            response_text = self.chat_with_openai(user_message)
            return JsonResponse({"response": response_text}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def chat_with_openai(self, prompt):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI interviewer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        return response['choices'][0]['message']['content']
