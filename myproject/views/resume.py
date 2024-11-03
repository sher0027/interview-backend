from myproject.utils import get_dynamodb_table
from rest_framework.views import APIView
from django.http import JsonResponse
from boto3.dynamodb.conditions import Key

class ResumeView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.users_table = get_dynamodb_table('resumes')  

    def get(self, request, *args, **kwargs):
        try:
            user_id = str(request.user.id)
            response = self.users_table.query(
                KeyConditionExpression=Key('uid').eq(user_id)
            )

            items = response.get('Items', [])
            if not items:
                return JsonResponse({"error": "Resume not found for the user."}, status=404)

            resume_info = items[0]
            return JsonResponse(resume_info, status=200)
        
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
        
    def put(self, request, *args, **kwargs):
        try:
            user_id = str(request.user.id)
            updated_resume = request.data  
            print(updated_resume)

            response = self.users_table.query(
                KeyConditionExpression=Key('uid').eq(user_id)
            )
            items = response.get('Items', [])
            if not items:
                return JsonResponse({"error": "Resume not found for the user."}, status=404)
            
            updated_resume['uid'] = user_id
            self.users_table.put_item(Item=updated_resume)
            
            return JsonResponse({"message": "Resume updated successfully."}, status=200)
        
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
