import os.path

import boto3
import pytest
from dotenv import load_dotenv
from PIL import Image

from ...bucket import upload_directory, upload_image_get_metadata
from ...settings import ROOT_DIR

load_dotenv()


class TestFunctionalBucket:
    abs_path = os.path.abspath(os.path.join(ROOT_DIR, '../..'))
    image_path = os.path.join(abs_path, "images", "27.586.1-cm-2016-02-09.tif")
    s3_path = "testing/"
    file_name = "27.586.1-cm-2016-02-09.tif"
    bucket_name = os.getenv('TEST_BUCKET')
    key = f"{s3_path}{file_name}"

    def test_functional_upload_image_get_metadata(self):
        default_session = boto3._get_default_session()
        image_metadata = upload_image_get_metadata(
            self.image_path, self.bucket_name, self.s3_path
        )
        assert image_metadata == self.key
        # cleanup
        s3 = default_session.client('s3')
        s3.delete_object(Bucket=self.bucket_name, Key=self.key)
        # TODO: think of way to integrate - assert cleaned_up_response[""]

    def test_functional_upload_directory(self):
        default_session = boto3._get_default_session()
        s3 = default_session.resource('s3')
        bucket = s3.Bucket(self.bucket_name)
        image_dir_path = os.path.join(self.abs_path, "images")
        upload_directory_response = upload_directory(
            image_dir_path, self.bucket_name, self.s3_path
        )
        assert upload_directory_response == None
        # cleanup s3
        bucket.objects.filter(Prefix=self.s3_path).delete()
