from django.http import JsonResponse
from rest_framework.views import APIView
from myproject.repositories.evaluation import EvaluationRepository


class EvaluationView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = EvaluationRepository()

    def get(self, request, eid, seq=None, *args, **kwargs):
        """
        Handle GET requests to fetch evaluations.
        """
        try:
            if seq:
                evaluation = self.repo.get_evaluation(eid, seq)
                if not evaluation:
                    return JsonResponse({"error": "Evaluation not found"}, status=404)
                return JsonResponse(evaluation, status=200)
            else:
                evaluations = self.repo.get_all_evaluations(eid)
                if not evaluations:
                    return JsonResponse({"error": "No evaluation found for the given eid"}, status=404)
                return JsonResponse({"evaluations": evaluations}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
