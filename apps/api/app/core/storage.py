import io
from typing import Optional
import boto3
from botocore.config import Config
from app.core.config import settings


def get_r2_s3_client():
    """
    Retorna cliente S3 configurado para Cloudflare R2 ou MinIO/AWS.
    """
    if not settings.S3_ACCESS_KEY or not settings.S3_SECRET_KEY:
        return None

    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL if settings.S3_ENDPOINT_URL else None,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION_NAME,
        config=Config(signature_version="s3v4"),
    )


def upload_file_to_r2(
    file_bytes: bytes,
    object_name: str,
    content_type: str = "application/xml",
) -> Optional[str]:
    """
    Realiza o upload de arquivo em bytes para o bucket Cloudflare R2.
    Retorna o nome da chave ou URL pública.
    """
    client = get_r2_s3_client()
    if not client or not settings.S3_BUCKET_NAME:
        # Fallback local se R2 não estiver parametrizado
        return object_name

    try:
        client.upload_fileobj(
            Fileobj=io.BytesIO(file_bytes),
            Bucket=settings.S3_BUCKET_NAME,
            Key=object_name,
            ExtraArgs={"ContentType": content_type},
        )
        return f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{object_name}"
    except Exception as e:
        print(f"Erro no upload para Cloudflare R2: {str(e)}")
        return None


def generate_presigned_download_url(object_name: str, expires_in: int = 3600) -> Optional[str]:
    """
    Gera link temporário seguro para download de XML/PDF no Cloudflare R2.
    """
    client = get_r2_s3_client()
    if not client or not settings.S3_BUCKET_NAME:
        return None

    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": object_name},
            ExpiresIn=expires_in,
        )
    except Exception as e:
        print(f"Erro ao gerar presigned URL no R2: {str(e)}")
        return None
