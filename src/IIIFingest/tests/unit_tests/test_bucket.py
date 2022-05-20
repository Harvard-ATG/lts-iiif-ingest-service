import os.path

import boto3
import pytest
from moto import mock_s3

from ...bucket import upload_directory, upload_image_get_metadata
from ...settings import ROOT_DIR

abs_path = os.path.abspath(os.path.join(ROOT_DIR, '../..'))
image_path = os.path.join(abs_path, "images", "27.586.1-cm-2016-02-09.tif")
s3_path="testing/"

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
        image_metadata = upload_image_get_metadata(image_path, self.test_bucket_name, s3_path)
        assert image_metadata == self.key

    def test_upload_directory(self):
        self.conn.create_bucket(Bucket=self.test_bucket_name)
        image_dir_path = os.path.join(abs_path, "images")
        upload_directory_response = upload_directory(image_dir_path, self.test_bucket_name, s3_path)
        assert upload_directory_response == None