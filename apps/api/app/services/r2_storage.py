import os
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("telesys.storage")


class CloudflareR2Storage:
    """
    Serviço de Armazenamento de Objetos em Bucket Cloudflare R2 / AWS S3.
    Se as chaves S3 não estiverem preenchidas no .env, realiza o fallback para o sistema de arquivos local.
    """

    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.region = settings.S3_REGION_NAME or "auto"

    @property
    def is_configured(self) -> bool:
        return bool(self.bucket and self.access_key and self.secret_key and self.endpoint_url)

    def upload_file(self, file_bytes: bytes, object_key: str, content_type: str = "application/octet-stream") -> bool:
        if not self.is_configured:
            logger.info(f"[Storage] R2 não configurado. Salvando em fallback local para o objeto: {object_key}")
            return False

        try:
            import boto3

            s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
            )

            s3_client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=file_bytes,
                ContentType=content_type,
            )
            logger.info(f"[Storage] Arquivo {object_key} enviado com sucesso para o Bucket Cloudflare R2 ({self.bucket})")
            return True
        except Exception as e:
            logger.error(f"[Storage] Erro ao enviar objeto para Cloudflare R2: {e}")
            return False

    def get_file_url(self, object_key: str) -> Optional[str]:
        if not self.is_configured:
            return None
        return f"{self.endpoint_url.rstrip('/')}/{self.bucket}/{object_key}"


r2_storage = CloudflareR2Storage()
