from myproject.utils.dynamoDB import get_dynamodb_table
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.conditions import Attr

class UserRepository:
    def __init__(self):
        self.table = get_dynamodb_table('users')

    def get_user(self, uid, version):
        """
        Retrieve a specific version of a user's resume.
        """
        response = self.table.get_item(Key={'uid': uid, 'version': int(version)})
        return response.get('Item')

    def get_all_versions(self, uid):
        """
        Retrieve all versions of resumes for a user.
        """
        response = self.table.query(KeyConditionExpression=Key('uid').eq(uid))
        return response.get('Items', [])
    
    def create_user(self, user_data):
        """
        Create a new user in the database.
        """
        self.table.put_item(Item=user_data)
    
    def upload_resume(self, uid, resume_data):
        try:
            response = self.table.query(
                KeyConditionExpression=Key('uid').eq(uid),
                ProjectionExpression="uid, username, password, version, s3_url",
                ScanIndexForward=False,
                Limit=1
            )

            if not response.get('Items'):
                raise ValueError(f"User with uid={uid} not registered.")

            latest_item = response['Items'][0]
            latest_version = latest_item['version']
            existing_s3_url = latest_item.get('s3_url')

            resume_data['uid'] = uid
            resume_data['username'] = latest_item['username']
            resume_data['password'] = latest_item['password']

            if latest_version == 1 and not existing_s3_url:
                resume_data['version'] = 1
                self.table.put_item(Item=resume_data)
                print("Updated empty resume for version: 1")
                return 1

            next_version = latest_version + 1
            resume_data['version'] = next_version
            self.table.put_item(Item=resume_data)
            print(f"Created new resume version: {next_version}")
            return next_version

        except ValueError as ve:
            print(f"Validation error: {ve}")
            raise
        except Exception as e:
            print(f"Error uploading resume: {e}")
            raise

    def save_resume(self, uid, version, updated_data):
        """
        Save (PUT) an updated resume for an existing `version`.
        """
        try:
            response = self.table.get_item(Key={'uid': uid, 'version': int(version)})
            if 'Item' not in response:
                raise ValueError(f"No resume found for uid={uid}, version={version}")

            restricted_fields = {"username", "password", "uid", "version"} 
            filtered_data = {key: value for key, value in updated_data.items() if key not in restricted_fields}

            if not filtered_data:
                raise ValueError("No updatable fields provided.")

            expression_attribute_names = {f"#{key}": key for key in filtered_data.keys()}
            expression_attribute_values = {f":{key}": value for key, value in filtered_data.items()}
            update_expression = "SET " + ", ".join([f"#{key} = :{key}" for key in filtered_data.keys()])

            self.table.update_item(
                Key={'uid': uid, 'version': int(version)},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,  
                ExpressionAttributeValues=expression_attribute_values
            )
            print(f"Resume for uid={uid}, version={version} updated successfully.")
        except Exception as e:
            print(f"Error saving resume: {e}")
            raise
