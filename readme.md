To start the backend:
1. conda activate 4347
2. pip install -r requirements.txt
3. python manage.py migrate
4. python manage.py runserver: will run on localhost:8000

To connect to apis and AWS service:
    create .env in root, should be like:
    `
    OPENAI_API_KEY=your-openai-api-key
    AWS_ACCESS_KEY_ID=your-aws-access-key
    AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
    AWS_STORAGE_BUCKET_NAME=your-aws-s3-bucket-name
    AWS_REGION_NAME=your-aws-region-name(ap-xxx-xx)
    `

