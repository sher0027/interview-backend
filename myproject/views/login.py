from django.http import JsonResponse
from myproject.utils import get_dynamodb_table
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from boto3.dynamodb.conditions import Attr

class LoginView(APIView):
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.users_table = get_dynamodb_table('users') 

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username:
            return JsonResponse({"error": "Username is required."}, status=400)
        if not password:
            return JsonResponse({"error": "Password is required."}, status=400)

        try:
            response = self.users_table.scan(
                FilterExpression=Attr('username').eq(username)
            )
            user_items = response.get('Items', [])
            if user_items:
                user = user_items[0]
                if user['password'] == password:  
                    user_obj, created = User.objects.get_or_create(username=username)
                    token, _ = Token.objects.get_or_create(user=user_obj)

                    return JsonResponse({
                        "message": "Login successful.",
                        "token": token.key
                    }, status=200)
                else:
                    return JsonResponse({"error": "Invalid username or password."}, status=401)
            else:
                return JsonResponse({"error": "User not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)