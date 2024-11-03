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
    records_table = get_dynamodb_table('records')
    resumes_table = get_dynamodb_table('resumes')

    def post(self, request, *args, **kwargs):
        rid = request.data.get("rid")
        company_info = request.data.get("companyInfo")

        if not rid or not company_info:
            return JsonResponse({"error": "Missing record ID or company information"}, status=400)

        try:
            resume_info = self.get_resume_info(request.user.id)
            if not resume_info:
                return JsonResponse({"error": "No resume found for the user"}, status=404)

            transcript = self.get_latest_transcript(rid)
            if not transcript:
                return JsonResponse({"error": "No transcript found for the given record ID"}, status=404)

            response_text = self.generate_interview_response(transcript, resume_info, company_info)
            self.save_reply(rid, response_text)

            return JsonResponse({"response": response_text}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def get_resume_info(self, uid):
        response = self.resumes_table.query(
            KeyConditionExpression=Key('uid').eq(str(uid))
        )
        return response['Items'][0] if 'Items' in response and response['Items'] else None

    def get_latest_transcript(self, rid):
        response = self.records_table.query(
            KeyConditionExpression=Key('rid').eq(rid),
            ProjectionExpression="seq, transcript",
            ScanIndexForward=False,
            Limit=1
        )
        return response['Items'][0].get('transcript') if 'Items' in response and response['Items'] else None

    def generate_interview_response(self, transcript, resume_info, company_info):
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
            {"role": "user", "content": transcript}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100
        )
        return response['choices'][0]['message']['content']

    def save_reply(self, rid, reply_text):
        response = self.records_table.query(
            KeyConditionExpression=Key('rid').eq(rid),
            ProjectionExpression="seq",
            ScanIndexForward=False,
            Limit=1
        )
        if 'Items' in response and response['Items']:
            latest_seq = response['Items'][0]['seq']
            
            self.records_table.update_item(
                Key={'rid': rid, 'seq': latest_seq},
                UpdateExpression="SET reply = :reply_text",
                ExpressionAttributeValues={':reply_text': reply_text}
            )

    
