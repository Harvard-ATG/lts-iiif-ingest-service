import argparse
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def upload_image_get_metadata(image_path, bucket_name, s3_path="", session=None):
    if not session:
        session = boto3._get_default_session()
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)

    file_dir, file_name = os.path.split(image_path)
    # make sure s3_path ends in a slash
    if s3_path and not s3_path.endswith("/"):
        s3_path += "/"

    # extend to handle in-memory later, once we have file upload on an application
    # https://thecodinginterface.com/blog/aws-s3-python-boto3/
    # bytes_data =
    # obj = s3.Object(bucket_name, f"{s3_path}{file_name}")
    # obj.put(Body=bytes_data)

    key = f"{s3_path}{file_name}" if s3_path else file_name

    # try to upload it
    try:
        bucket.upload_file(Filename=image_path, Key=key)
        return key
    except ClientError as e:
        logging.error(e)
        return False


def upload_directory(path, bucket_name, session=None):
    if not session:
        session = boto3._get_default_session()
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)

    for subdir, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(subdir, file)
            with open(full_path, 'rb') as data:
                bucket.put_object(Key=full_path[len(path) + 1 :], Body=data)


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
        response = upload_image_get_metadata(
            args.file, args.bucket, s3_path=args.s3path
        )
        print(response)
