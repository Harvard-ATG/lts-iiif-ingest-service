import pytest
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import ClientError
from moto import mock_s3

from IIIFingest.bucket import upload_directory, upload_image_get_metadata

s3_path = "testing/"


@mock_s3
class TestBucket:
    test_bucket_name = 'iiif-ingest-test-bucket'
    file_name = "27.586.1-cm-2016-02-09.tif"
    key = f"{s3_path}{file_name}"

    def test_upload_image_get_metadata(self, test_images, boto_session):
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        image_path = test_images[self.file_name]["filepath"]
        boto_session.resource('s3').create_bucket(Bucket=self.test_bucket_name)
        image_metadata = upload_image_get_metadata(
            image_path, self.test_bucket_name, s3_path
        )
        assert image_metadata == self.key

    def test_fail_upload_image_get_metadata(self, test_images):
        image_path = test_images[self.file_name]["filepath"]
        with pytest.raises(S3UploadFailedError):
            assert upload_image_get_metadata(image_path, self.test_bucket_name, s3_path)

    def test_upload_directory(self, images_dir, boto_session):
        boto_session.resource('s3').create_bucket(Bucket=self.test_bucket_name)
        upload_directory_response = upload_directory(
            images_dir, self.test_bucket_name, s3_path
        )
        assert upload_directory_response is not False

    def test_fail_upload_directory(self, images_dir):
        with pytest.raises(ClientError):
            assert upload_directory(images_dir, self.test_bucket_name, s3_path)