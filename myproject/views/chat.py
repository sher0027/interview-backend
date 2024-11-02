import openai
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from boto3.dynamodb.conditions import Key
from myproject import settings
from myproject.utils import get_dynamodb_table

openai.api_key = settings.OPENAI_API_KEY 

class ChatView(APIView):
    parser_classes = [JSONParser]
    table = get_dynamodb_table('records') 

    def post(self, request, *args, **kwargs):
        rid = request.data.get("rid") 
        if not rid:
            return JsonResponse({"error": "No record ID (rid) provided"}, status=400)

        try:
            transcript = self.get_latest_transcript(rid)
            if not transcript:
                return JsonResponse({"error": "No transcript found for the given rid"}, status=404)

            response_text = self.chat_with_openai(transcript, company_info, resume_text)
            self.save_reply(rid, response_text)

            return JsonResponse({"response": "Reply saved successfully"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def get_latest_transcript(self, rid):
        """Fetches the latest transcript for the given record ID (rid)"""
        response = self.table.query(
            KeyConditionExpression=Key('rid').eq(rid),
            ProjectionExpression="seq, transcript",
            ScanIndexForward=False,  
            Limit=1
        )
        if 'Items' in response and response['Items']:
            return response['Items'][0].get('transcript')  
        return None

    def chat_with_openai(self, transcript, company_info, resume_text):
        company_name = company_info.get("name", "Unknown Company")
        role_name = company_info.get("role", "Unknown Role")
        job_description = company_info.get("description", "No job description available")

        messages = [
            {
                "role": "system",
                "content": (
                    f"You are an interviewer from {company_name}.\n"
                    f"A candidate is interviewing for the position of {role_name}.\n"
                    f"Job Description: {job_description}\n"
                    f"Resume: {resume_text}\n"
                    "Please ask relevant interview questions based on the candidate's resume and responses.\n"
                    "Begin with a general question such as 'Tell me about yourself', then proceed with questions one by one."
                )
            },
            {"role": "user", "content": transcript}
        ]
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150  
        )
        return response['choices'][0]['message']['content']
    
    def save_reply(self, rid, reply_text):
        """Saves the AI's reply in the database for the latest sequence under the specified record ID (rid)"""
        response = self.table.query(
            KeyConditionExpression=Key('rid').eq(rid),
            ProjectionExpression="seq",
            ScanIndexForward=False, 
            Limit=1
        )
        
        # Check if there's a latest item to update
        if 'Items' in response and response['Items']:
            latest_seq = response['Items'][0]['seq']
            # Update reply field in the latest transcript entry
            self.table.update_item(
                Key={'rid': rid, 'seq': latest_seq},
                UpdateExpression="SET reply = :reply_text",
                ExpressionAttributeValues={':reply_text': reply_text}
            )
