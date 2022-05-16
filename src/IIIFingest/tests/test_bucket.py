import boto3
import pytest
import os.path
from PIL import Image
from dotenv import load_dotenv

from ..bucket import upload_image_get_metadata

load_dotenv()

abs_path = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(abs_path, "images", "27.586.1-cm-2016-02-09.tif")
s3_path="testing/"
file_name = "27.586.1-cm-2016-02-09.tif"
# move to .env file
bucket_name = os.getenv('TEST_BUCKET')
key = f"{s3_path}{file_name}"
def clean_up(bucket_name, key):
    session = boto3._get_default_session()
    s3 = session.client('s3')
    delete = s3.delete_object(Bucket=bucket_name, Key=key)
    return delete


def test_upload_image_get_metadata():
    image_metadata = upload_image_get_metadata(image_path, bucket_name, s3_path)
    assert image_metadata == key
    clean_up(bucket_name, key)
    # TODO: think of way to integrate - assert cleaned_up_response[""]