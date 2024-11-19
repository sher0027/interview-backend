from myproject.utils.dynamoDB import get_dynamodb_table
from boto3.dynamodb.conditions import Key

class EvaluationRepository:
    def __init__(self):
        self.table = get_dynamodb_table('evaluations')

    def get_evaluation(self, eid, seq):
        """
        Retrieve a specific evaluation by its evaluation ID (eid) and sequence number (seq).
        """
        response = self.table.get_item(Key={'eid': eid, 'seq': int(seq)})
        return response.get('Item')

    def get_all_evaluations(self, eid):
        """
        Retrieve all evaluations associated with a specific evaluation ID (eid).
        """
        response = self.table.query(KeyConditionExpression=Key('eid').eq(eid))
        return response.get('Items', [])

    def save_acoustic_evaluation(self, eid, seq, acoustic_result):
        """
        Save the results of acoustic evaluation.
        """
        self.table.update_item(
            Key={'eid': eid, 'seq': seq},
            UpdateExpression="SET acoustic = :acoustic_result",
            ExpressionAttributeValues={':acoustic_result': acoustic_result}
        )

    def save_content_evaluation(self, eid, seq, content_result):
        """
        Save the results of content evaluation.
        """
        self.table.update_item(
            Key={'eid': eid, 'seq': seq},
            UpdateExpression="SET content = :content_result",
            ExpressionAttributeValues={':content_result': content_result}
        )

   
