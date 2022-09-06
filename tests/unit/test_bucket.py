import pytest
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import ClientError
from moto import mock_s3

from IIIFingest.bucket import (
    upload_directory,
    upload_image_by_fileobj,
    upload_image_by_filepath,
    upload_image_get_metadata,
)

s3_path = "testing/"


@mock_s3
class TestBucket:
    test_bucket_name = 'iiif-ingest-test-bucket'
    file_name = "27.586.1-cm-2016-02-09.tif"
    key = f"{s3_path}{file_name}"

    def test_upload_image_by_filepath(self, test_images, boto_session):
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        image_path = test_images[self.file_name]["filepath"]
        boto_session.resource('s3').create_bucket(Bucket=self.test_bucket_name)
        image_metadata = upload_image_by_filepath(
            image_path, self.test_bucket_name, s3_path
        )
        assert image_metadata == self.key

    def test_fail_upload_image_by_filepath(self, test_images):
        image_path = test_images[self.file_name]["filepath"]
        with pytest.raises(S3UploadFailedError):
            assert upload_image_by_filepath(image_path, self.test_bucket_name, s3_path)

    def test_upload_image_by_fileobj(self, test_images, boto_session):
        """
        Upload should succeed with a basic file object. If it succeeds here,
        that should also mean that it will succeed with a Django File or
        UploadedFile object, which have the same attributes and methods, plus
        additional django-specific functionality.
        """
        s3 = boto_session.resource('s3')
        s3.create_bucket(Bucket=self.test_bucket_name)
        with open(test_images[self.file_name]['filepath'], "rb") as fileobj:
            image_s3_key = upload_image_by_fileobj(
                fileobj, self.file_name, self.test_bucket_name, s3_path
            )
        # Verify output of upload function
        assert image_s3_key == self.key

    def test_fail_upload_image_by_fileobj(self, test_images):
        """
        This tests to make sure that an upload fails when the bucket is not
        present, which also makes sure that errors are being passed up
        accurately. The botocore errorfactory should produce an error class for
        this error, but we can catch it as a general ClientError and make sure
        that the error code is what's expected.
        """
        with open(test_images[self.file_name]['filepath'], "rb") as fileobj:
            try:
                # this block should fail
                upload_image_by_fileobj(
                    fileobj,
                    self.file_name,
                    self.test_bucket_name,
                    s3_path)
            except ClientError as e:
                assert e.response['Error']['Code'] == "NoSuchBucket"

    def test_deprecated_upload(self, test_images, boto_session):
        """
        Make sure that the deprecated `upload_image_get_metadata` function
        raises a deprecation warning when called.
        """
        image_path = test_images[self.file_name]["filepath"]
        boto_session.resource('s3').create_bucket(Bucket=self.test_bucket_name)
        with pytest.deprecated_call():
            upload_image_get_metadata(
                image_path, self.test_bucket_name, s3_path
            )

    def test_upload_directory(self, images_dir, boto_session):
        boto_session.resource('s3').create_bucket(Bucket=self.test_bucket_name)
        upload_directory_response = upload_directory(
            images_dir, self.test_bucket_name, s3_path
        )
        assert upload_directory_response is not False

    def test_fail_upload_directory(self, images_dir):
        with pytest.raises(ClientError):
            assert upload_directory(images_dir, self.test_bucket_name, s3_path)
