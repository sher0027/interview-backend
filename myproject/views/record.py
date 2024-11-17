from rest_framework.views import APIView
from django.http import JsonResponse
from myproject.repositories.record import RecordRepository

class RecordView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = RecordRepository()

    def get(self, request, rid, seq=None, *args, **kwargs):
        try:
            if seq:
                record = self.repo.get_record(rid, seq)
                if not record:
                    return JsonResponse({"error": "Record not found"}, status=404)
                return JsonResponse(record, status=200)
            else:
                records = self.repo.get_all_records(rid)
                if not records:
                    return JsonResponse({"error": "No record found for the given rid"}, status=404)
                return JsonResponse({"records": records}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
   