from rest_framework.views import APIView
from django.http import JsonResponse
from myproject.repositories.user import UserRepository


class ResumeView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = UserRepository()

    def get(self, request, version=None, *args, **kwargs):
        """
        Handle GET requests to retrieve a user's resume(s).

        If `version` is provided, retrieves a specific resume version for the user.
        Otherwise, retrieves all resume versions for the user.
        """
        try:
            uid = str(request.user.id)
            if version:
                resume = self.repo.get_user(uid, version)
                if not resume:
                    return JsonResponse({"error": "No resume found for the given version."}, status=404)
                return JsonResponse(resume, status=200)
            else:
                resumes = self.repo.get_all_versions(uid)
                if not resumes:
                    return JsonResponse({"error": "No resumes found for the user."}, status=404)
                return JsonResponse({"resumes": resumes}, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    def put(self, request, version, *args, **kwargs):
        """
        Handle PUT requests to update an existing resume.

        Expects the `version` in the request data to identify which resume to update.
        """
        try:
            if not version:
                return JsonResponse({"error": "Version is required to update a resume."}, status=400)
            
            uid = str(request.user.id) 
            updated_resume = request.data  
            existing_resume = self.repo.get_user(uid, version)
            if not existing_resume:
                return JsonResponse({"error": "Resume not found for the specified version."}, status=404)

            self.repo.save_resume(uid, version, updated_resume)

            return JsonResponse({"message": "Resume updated successfully."}, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
