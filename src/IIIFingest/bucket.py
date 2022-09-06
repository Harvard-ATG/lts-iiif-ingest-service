import argparse
import base64
import hashlib
import logging
import os
from typing import BinaryIO

import boto3
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import ClientError
from deprecated import deprecated

logger = logging.getLogger(__name__)


def upload_image_by_filepath(
    filepath: str, bucket_name: str, s3_path: str = "", session: boto3.Session = None
) -> str:
    """
    Upload an image to S3 using a path to a file on disk.
    """
    # Set up boto3 session, if need be
    if not session:
        session = boto3._get_default_session()
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)

    _, file_name = os.path.split(filepath)
    # make sure s3_path ends in a slash
    if s3_path and not s3_path.endswith("/"):
        s3_path += "/"

    key = f"{s3_path}{file_name}" if s3_path else file_name

    # try to upload it
    try:
        bucket.upload_file(Filename=filepath, Key=key)
        return key

    except S3UploadFailedError as e:
        logging.error(e)
        raise e


def upload_image_by_fileobj(
    fileobj: BinaryIO,
    filename: str,
    bucket_name: str,
    s3_path: str = "",
    session: boto3.Session = None,
) -> str:
    """
    Upload an image to S3 using a file object in memory.
    """
    # Set up boto3 session, if need be
    if not session:
        session = boto3._get_default_session()
    s3 = session.client('s3')

    # make sure s3_path ends in a slash
    if s3_path and not s3_path.endswith("/"):
        s3_path += "/"

    # set key from path and filename
    key = f"{s3_path}{filename}" if s3_path else filename

    # Get an md5 hash of the object to verify the upload
    fileobj.seek(0)
    digest = hashlib.md5(fileobj.read()).digest()
    hash = base64.b64encode(digest).decode('utf-8')
    fileobj.seek(0)

    # try to upload it
    try:
        s3.put_object(Bucket=bucket_name, Body=fileobj, ContentMD5=hash, Key=key)
        return key
    except S3UploadFailedError as e:
        logging.error(e)
        raise e


@deprecated(
    version='1.1.0',
    reason="This function is deprecated, use `upload_image_by_filepath` instead",
)
def upload_image_get_metadata(
    filepath: str, bucket_name: str, s3_path: str = "", session: boto3.Session = None
) -> str:
    return upload_image_by_filepath(filepath, bucket_name, s3_path, session)


def upload_directory(path, bucket_name, s3_path="", session=None):
    if s3_path and not s3_path.endswith("/"):
        s3_path += "/"
    if not session:
        session = boto3._get_default_session()
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)
    try:
        for subdir, dirs, files in os.walk(path):
            for file in files:
                full_path = os.path.join(subdir, file)
                with open(full_path, 'rb') as data:
                    bucket_file_path = full_path[len(path) + 1 :]
                    bucket.put_object(
                        Key=f"{s3_path}{bucket_file_path}"
                        if s3_path
                        else bucket_file_path,
                        Body=data,
                    )
        return True
    except ClientError as e:
        logging.error(e)
        raise e


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", "-d", help="set directory")
    parser.add_argument("--bucket", "-b", help="set bucket")
    parser.add_argument("--file", "-f", help="set single file for upload")
    parser.add_argument("--s3path", help="Optional S3 path")
    args = parser.parse_args()

    if not args.bucket:
        print("Please set a bucket which you can use in the current AWS session")

    if args.dir and args.bucket:
        upload_directory(args.dir, args.bucket)

    if args.file and args.bucket:
        response = upload_image_by_filepath(args.file, args.bucket, s3_path=args.s3path)
        print(response)
