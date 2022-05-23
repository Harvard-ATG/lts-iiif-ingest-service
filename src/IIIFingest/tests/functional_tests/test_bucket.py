import os.path

import boto3
import pytest
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import ClientError
from dotenv import load_dotenv

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
    default_session = boto3._get_default_session()
    image_dir_path = os.path.join(abs_path, "images")

    def test_functional_upload_image_get_metadata(self):
        image_metadata = upload_image_get_metadata(
            self.image_path, self.bucket_name, self.s3_path
        )
        assert image_metadata == self.key
        # cleanup
        s3 = self.default_session.client('s3')
        s3.delete_object(Bucket=self.bucket_name, Key=self.key)
        # TODO: think of way to integrate - assert cleaned_up_response[""]

    def test_fail_upload_image_get_metadata(self):
        bucket = "doesnotexist"
        with pytest.raises(S3UploadFailedError):
            assert upload_image_get_metadata(self.image_path, bucket, self.s3_path)

    def test_functional_upload_directory(self):
        default_session = boto3._get_default_session()
        s3 = default_session.resource('s3')
        bucket = s3.Bucket(self.bucket_name)

        upload_directory_response = upload_directory(
            self.image_dir_path, self.bucket_name, self.s3_path
        )
        assert upload_directory_response is not False
        # cleanup s3
        bucket.objects.filter(Prefix=self.s3_path).delete()

    def test_functional_fail_upload_directory(self):
        bucket = "doesnotexist"
        with pytest.raises(ClientError):
            assert upload_directory(self.image_dir_path, bucket, self.s3_path)
