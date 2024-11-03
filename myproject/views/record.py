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

    def update_reply(self, rid, reply_text):
        try:
            response = self.records_table.query(
                KeyConditionExpression=Key('rid').eq(rid),
                ProjectionExpression="seq",
                ScanIndexForward=False,
                Limit=1
            )
            if 'Items' not in response or not response['Items']:
                return JsonResponse({"error": "No record found to update reply"}, status=404)

            latest_seq = response['Items'][0]['seq']

            self.records_table.update_item(
                Key={'rid': rid, 'seq': latest_seq},
                UpdateExpression="SET reply = :reply_text",
                ExpressionAttributeValues={':reply_text': reply_text}
            )

            return JsonResponse({"message": "Reply updated successfully"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
