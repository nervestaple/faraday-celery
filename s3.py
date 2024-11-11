import os
from dotenv import load_dotenv
import requests
import boto3

from uuid_extensions import uuid7str
from botocore.exceptions import NoCredentialsError

load_dotenv()

s3 = boto3.client(
  's3',
  aws_access_key_id=os.getenv('AWS_S3_ACCESS_KEY_ID'),
  aws_secret_access_key=os.getenv('AWS_S3_SECRET_ACCESS_KEY')
)
warranty_bucket_name = os.getenv('AWS_S3_BUCKET_NAME')


def upload_warranty_pdf_to_s3(file_url):
  response = requests.get(file_url)
  key = f"warranty-{uuid7str()}.pdf"

  try:
    s3.put_object(
      Bucket=warranty_bucket_name,
      Key=key,
      Body=response.content,
      ContentType='application/pdf'
    )
    file_url = f"https://{warranty_bucket_name}.s3.amazonaws.com/{key}"
    return file_url
  except NoCredentialsError:
    print("Credentials not available")
    return None
