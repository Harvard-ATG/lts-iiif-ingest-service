import os
import logging
import boto3
from settings import ROOT_DIR
import sys, argparse

logger = logging.getLogger(__name__)

def upload_directory(path, bucket_name, session=None):
    if not session:
        session = boto3._get_default_session()
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)

    for subdir, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(subdir, file)
            with open(full_path, 'rb') as data:
                bucket.put_object(Key=full_path[len(path)+1:], Body=data)


if __name__ == "__main__":
    print(f"Arguments count: {len(sys.argv)}")
    for i, arg in enumerate(sys.argv):
        print(f"Argument {i:>6}: {arg}")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", "-d", help="set directory")
    parser.add_argument("--bucket", "-b", help="set bucket")
    args = parser.parse_args()

    upload_directory(args.dir, args.bucket)