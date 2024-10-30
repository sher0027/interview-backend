import os
import openai
import json
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.conf import settings

 

@api_view(['POST'])
def send_chat_message(request):
    if request.method == 'POST':
        prompt = request.data.get('prompt')
        if not prompt:
            return JsonResponse({'error': 'No prompt provided'}, status=400)

        try:
            response = openai.completions.create(
                model="gpt-3.5-turbo",
                prompt=prompt,
                max_tokens=150
            )
            return JsonResponse(response['choices'][0]['message']['content'], safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
