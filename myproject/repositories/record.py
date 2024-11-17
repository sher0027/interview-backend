from myproject.utils.dynamoDB import get_dynamodb_table
from boto3.dynamodb.conditions import Key

class RecordRepository:
    def __init__(self):
        self.table = get_dynamodb_table('records')

    def get_record(self, rid, seq):
        """
        Retrieve a specific record by its record ID (rid) and sequence number (seq).
        """
        response = self.table.get_item(Key={'rid': rid, 'seq': int(seq)})
        return response.get('Item')

    def get_all_records(self, rid):
        """
        Retrieve all records associated with a specific record ID (rid).
        """
        response = self.table.query(KeyConditionExpression=Key('rid').eq(rid))
        return response.get('Items', [])
    
    def get_next_sequence(self, rid):
        """
        Retrieve the next available sequence number for a given record ID (rid).
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key('rid').eq(rid),
                ProjectionExpression="seq",
                ScanIndexForward=False,  
                Limit=1  
            )
            if 'Items' in response and response['Items']:
                latest_seq = response['Items'][0]['seq']
                return latest_seq + 1
            else:
                return 1
        except Exception as e:
            print(f"Error getting next sequence: {e}")
            raise

    def save_record(self, rid, seq, transcript, s3_url):
        """
        Save a new record into the 'records' table.
        """
        self.table.put_item(Item={
            'rid': rid,
            'seq': seq,
            'transcript': transcript,
            's3_url': s3_url
        })

    def update_reply(self, rid, seq, reply_text):
        """
        Update the reply field of a specific record.
        """
        self.table.update_item(
            Key={'rid': rid, 'seq': seq},
            UpdateExpression="SET reply = :reply_text",
            ExpressionAttributeValues={':reply_text': reply_text}
        )
