import boto3


from app.core.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
    )


def get_s3_public_client(object_key: str) -> str:
    s3_public = boto3.client(
        "s3",
        endpoint_url=settings.s3_public_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
    )
    return s3_public


def upload_fileobj(file_obj, object_key: str, content_type: str | None = None):
    s3 = get_s3_client()
    extra_args = {}

    if content_type:
        extra_args["ContentType"] = content_type

    if extra_args:
        s3.upload_fileobj(
            Fileobj=file_obj,
            Bucket=settings.s3_bucket,
            Key=object_key,
            ExtraArgs=extra_args,
        )
    else:
        s3.upload_fileobj(
            Fileobj=file_obj,
            Bucket=settings.s3_bucket,
            Key=object_key,
        )


def download_object_to_path(object_key: str, target_path: str):
    s3 = get_s3_client()
    s3.download_file(
        Bucket=settings.s3_bucket,
        Key=object_key,
        Filename=target_path,
    )