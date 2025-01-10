import boto3
from app.core.logger import logger
from app.core.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION_NAME,BUCKET_NAME
from fastapi import HTTPException


s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION_NAME
)
BUCKET_NAME = BUCKET_NAME
def upload_image_to_s3(image,image_name):
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=image_name,
            Body=image,
            ContentType="image/jpeg"
        )
    except Exception as e:
        logger.error(f"Error while uploading image to S3: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")