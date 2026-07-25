import os

import aioboto3
from botocore.config import Config


class StorageService:
    def __init__(self):
        self.session = aioboto3.Session()
        self.endpoint_url = os.getenv("MESA_LAW_STORAGE_ENDPOINT", "http://localhost:9000")
        self.aws_access_key_id = os.getenv("MESA_LAW_STORAGE_ACCESS_KEY", "admin")
        self.aws_secret_access_key = os.getenv("MESA_LAW_STORAGE_SECRET_KEY", "password123")
        self.bucket_name = os.getenv("MESA_LAW_STORAGE_BUCKET", "mesa-law-docs")
        self.config = Config(signature_version="s3v4")
    
    async def create_bucket_if_not_exists(self):
        async with self.session.client('s3', endpoint_url=self.endpoint_url,
                                     aws_access_key_id=self.aws_access_key_id,
                                     aws_secret_access_key=self.aws_secret_access_key,
                                     config=self.config) as s3:
            try:
                await s3.head_bucket(Bucket=self.bucket_name)
            except s3.exceptions.ClientError:
                await s3.create_bucket(Bucket=self.bucket_name)

    async def generate_presigned_upload_url(self, object_key: str, mime_type: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for PUT operation.
        This gives frontend intent to upload a file directly to MinIO.
        """
        async with self.session.client('s3', endpoint_url=self.endpoint_url,
                                     aws_access_key_id=self.aws_access_key_id,
                                     aws_secret_access_key=self.aws_secret_access_key,
                                     config=self.config) as s3:
            url = await s3.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key,
                    'ContentType': mime_type
                },
                ExpiresIn=expires_in
            )
            return url
            
    async def generate_presigned_download_url(self, object_key: str, expires_in: int = 3600) -> str:
        async with self.session.client('s3', endpoint_url=self.endpoint_url,
                                     aws_access_key_id=self.aws_access_key_id,
                                     aws_secret_access_key=self.aws_secret_access_key,
                                     config=self.config) as s3:
            url = await s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expires_in
            )
            return url

storage_service = StorageService()
