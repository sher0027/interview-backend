from myproject.utils import get_dynamodb_table
from rest_framework.views import APIView
from django.http import JsonResponse
from boto3.dynamodb.conditions import Key

class RecordView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.records_table = get_dynamodb_table('records')  

    def get(self, request, rid, seq=None, *args, **kwargs):
        try:
            if seq:
                response = self.records_table.get_item(
                    Key={'rid': rid, 'seq': int(seq)}
                )
                item = response.get('Item')
                if not item:
                    return JsonResponse({"error": "Record not found"}, status=404)
                return JsonResponse(item, status=200)
            else:
                response = self.records_table.query(
                    KeyConditionExpression=Key('rid').eq(rid)
                )
                items = response.get('Items', [])
                if not items:
                    return JsonResponse({"error": "No records found for the given rid"}, status=404)
                return JsonResponse({"records": items}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
