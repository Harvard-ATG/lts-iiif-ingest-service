import os.path

import boto3
import pytest
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import ClientError
from moto import mock_s3

from IIIFingest.bucket import upload_directory, upload_image_get_metadata

TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(TESTS_DIR, "images")

image_path = os.path.join(IMAGES_DIR, "27.586.1-cm-2016-02-09.tif")
s3_path = "testing/"


@mock_s3
class TestBucket:
    test_bucket_name = 'testbucket'
    file_name = "27.586.1-cm-2016-02-09.tif"
    key = f"{s3_path}{file_name}"

    @pytest.fixture(autouse=True, scope='class')
    def setup_conn(self):
        self.__class__.conn = boto3.resource('s3', region_name='us-east-1')

    def test_upload_image_get_metadata(self):
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        self.conn.create_bucket(Bucket=self.test_bucket_name)
        image_metadata = upload_image_get_metadata(
            image_path, self.test_bucket_name, s3_path
        )
        assert image_metadata == self.key

    def test_fail_upload_image_get_metadata(self):
        with pytest.raises(S3UploadFailedError):
            assert upload_image_get_metadata(image_path, self.test_bucket_name, s3_path)

    def test_upload_directory(self):
        self.conn.create_bucket(Bucket=self.test_bucket_name)
        image_dir_path = IMAGES_DIR
        upload_directory_response = upload_directory(
            image_dir_path, self.test_bucket_name, s3_path
        )
        assert upload_directory_response is not False

    def test_fail_upload_directory(self):
        image_dir_path = IMAGES_DIR
        with pytest.raises(ClientError):
            assert upload_directory(image_dir_path, self.test_bucket_name, s3_path)
