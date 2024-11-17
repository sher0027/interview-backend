from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from myproject.repositories.user import UserRepository

class AuthView(APIView):
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = UserRepository()

    def post(self, request, *args, **kwargs):
        """
        Handle login or registration based on 'action' parameter.
        """
        action = request.data.get("action")
        if action == "login":
            return self._login(request)
        elif action == "register":
            return self._register(request)
        else:
            return JsonResponse({"error": "Invalid action. Use 'login' or 'register'."}, status=400)

    def _login(self, request):
        """
        Handle user login.
        """
        username, password, error_response = self._validate_credentials(request)
        if error_response:
            return error_response

        try:
            user = User.objects.filter(username=username).first()
            if user and check_password(password, user.password):
                refresh = RefreshToken.for_user(user) 
                return JsonResponse({
                    "message": "Login successful.",
                    "access": str(refresh.access_token), 
                    "refresh": str(refresh), 
                }, status=200)
            else:
                return JsonResponse({"error": "Invalid username or password."}, status=401)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def _register(self, request):
        """
        Handle user registration.
        """
        username, password, error_response = self._validate_credentials(request)
        if error_response:
            return error_response

        try:
            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username already exists."}, status=400)

            user = User(username=username)
            user.set_password(password)
            user.save()

            user_data = {
                'uid': str(user.id),
                'username': username,
                'password': user.password,
                'version': 1
            }
            self.repo.create_user(user_data)

            refresh = RefreshToken.for_user(user)  
            return JsonResponse({
                "message": "Registration successful.",
                "access": str(refresh.access_token), 
                "refresh": str(refresh), 
                "uid": user.id
            }, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def _validate_credentials(self, request):
        """
        Validate the username and password from the request data.
        """
        username = request.data.get("username")
        password = request.data.get("password")

        if not username:
            return None, None, JsonResponse({"error": "Username is required."}, status=400)
        if not password:
            return None, None, JsonResponse({"error": "Password is required."}, status=400)

        return username, password, None
