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

    def save_evaluation(self, eid, seq, evaluation_result):
        """
        Save a new evaluation result into the 'evaluations' table.
        """
        self.table.put_item(Item={
            'eid': eid,
            'seq': seq,
            'evaluation_result': evaluation_result
        })

   
