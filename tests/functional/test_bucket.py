import os.path

import boto3
import pytest
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import ClientError

from IIIFingest.bucket import upload_directory, upload_image_by_filepath

TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(TESTS_DIR, "images")


class TestFunctionalBucket:
    image_path = os.path.join(IMAGES_DIR, "27.586.1-cm-2016-02-09.tif")
    s3_path = "testing/"
    file_name = "27.586.1-cm-2016-02-09.tif"
    bucket_name = os.getenv('TEST_BUCKET')
    test_aws_profile = os.getenv('TEST_AWS_PROFILE')
    key = f"{s3_path}{file_name}"
    default_session = boto3.Session(profile_name=test_aws_profile)
    image_dir_path = IMAGES_DIR

    def test_functional_upload_image_by_filepatha(self):
        image_metadata = upload_image_by_filepath(
            self.image_path, self.bucket_name, self.s3_path, self.default_session
        )
        assert image_metadata == self.key
        # cleanup
        s3 = self.default_session.client('s3')
        s3.delete_object(Bucket=self.bucket_name, Key=self.key)
        # TODO: think of way to integrate - assert cleaned_up_response[""]

    def test_fail_upload_image_by_filepath(self):
        bucket = "doesnotexist"
        with pytest.raises(S3UploadFailedError):
            assert upload_image_by_filepath(self.image_path, bucket, self.s3_path)

    def test_functional_upload_directory(self):
        s3 = self.default_session.resource('s3')
        bucket = s3.Bucket(self.bucket_name)

        upload_directory_response = upload_directory(
            self.image_dir_path, self.bucket_name, self.s3_path, self.default_session
        )
        assert upload_directory_response is not False
        # cleanup s3
        bucket.objects.filter(Prefix=self.s3_path).delete()

    def test_functional_fail_upload_directory(self):
        bucket = "doesnotexist"
        with pytest.raises(ClientError):
            assert upload_directory(self.image_dir_path, bucket, self.s3_path)
