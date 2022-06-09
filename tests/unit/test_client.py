from email.policy import default
import os.path

from botocore.exceptions import ClientError
import pytest

from moto import mock_s3
from dotenv import load_dotenv

import re
from IIIFingest.client import Client

load_dotenv()


@mock_s3
class TestClient:
    test_aws_profile = os.getenv('TEST_AWS_PROFILE', default="tester")
    bucket_name = os.getenv('TEST_BUCKET', default="fake.school.it.lts.mps.testing-dev")

    # Define manifest-level metadata
    manifest_level_metadata = {
        "labels": ["Test Manifest"],
        "summary": "A test manifest for ingest",
        "rights": "http://creativecommons.org/licenses/by-sa/3.0/",
    }

    def test_client_upload(self, test_images, boto_session, test_client):
        boto_session.resource('s3').create_bucket(Bucket=self.bucket_name)

        image_path = test_images["27.586.1-cm-2016-02-09.tif"]["filepath"]

        client = test_client

        images = [{"label": "Test Image", "filepath": image_path}]
        assets = client.upload(images, s3_path="testing")

        assert assets is not None
        assert assets[0].filepath == image_path
        clean_up_delete_s3_bucket(boto_session=boto_session, bucket=self.bucket_name)

    def test_client_fail_upload(self, test_images, boto_session, test_client):
        with pytest.raises(ClientError):
            boto_session.client('s3').delete_bucket(Bucket=self.bucket_name)
            image_path = test_images["27.586.1-cm-2016-02-09.tif"]["filepath"]

            client = test_client

            images = [{"label": "Test Image", "filepath": image_path}]
            assert client.upload(images, s3_path="testing")

    def test_client_create_manifest(self, test_images, boto_session, test_client):
        boto_session.resource('s3').create_bucket(Bucket=self.bucket_name)
        client = test_client
        image_path = test_images["27.586.1-cm-2016-02-09.tif"]["filepath"]
        images = [{"label": "Test Image", "filepath": image_path}]
        assets = client.upload(images, s3_path="testing")
        """
        Example of the assets list of dict
        assets = [
            {
                'asset_id': 'testTMf2nGLoepAPr2tvEpw6EA',
                'extension': '.tiff',
                'filepath': '/Users/vtan/harvard-atg/lts-iiif-ingest-service/images/27.586.1-cm-2016-02-09.tif',
                'format': 'image/tiff',
            }
        ]
        """

        manifest = client.create_manifest(
            manifest_level_metadata=self.manifest_level_metadata, assets=assets
        )
        root_id = "https://nrs-dev.lib.harvard.edu/URN-3:AT:"
        matches_root_id = re.search(root_id, manifest["id"])
        item = manifest["items"][0]
        assert len(manifest["items"]) == 1
        assert matches_root_id is not None
        assert item["height"] == 564 and item["width"] == 3600
        clean_up_delete_s3_bucket(boto_session=boto_session, bucket=self.bucket_name)

    def test_client_fail_create_manifest_missing_asset(
        self, test_images, boto_session, test_client
    ):
        with pytest.raises(TypeError):

            boto_session.resource('s3').create_bucket(Bucket=self.bucket_name)
            client = test_client
            image_path = test_images["27.586.1-cm-2016-02-09.tif"]["filepath"]
            images = [{"label": "Test Image", "filepath": image_path}]
            assert client.create_manifest(
                manifest_level_metadata=self.manifest_level_metadata,
            )
            clean_up_delete_s3_bucket(boto_session=boto_session, bucket=self.bucket_name)

    def test_client_fail_create_manifest_missing_meta_data(
        self, test_images, boto_session, test_client
    ):
        with pytest.raises(TypeError):

            boto_session.resource('s3').create_bucket(Bucket=self.bucket_name)
            client = test_client
            image_path = test_images["27.586.1-cm-2016-02-09.tif"]["filepath"]
            images = [{"label": "Test Image", "filepath": image_path}]
            assets = client.upload(images, s3_path="testing")
            assert client.create_manifest(assets=assets)
            clean_up_delete_s3_bucket(boto_session=boto_session, bucket=self.bucket_name)

# TODO move to fixture that accepts params - https://docs.pytest.org/en/latest/example/parametrize.html#apply-indirect-on-particular-arguments
def clean_up_delete_s3_bucket(boto_session, bucket):
    s3 =  boto_session.resource('s3')
    bucket = s3.Bucket(bucket)
    bucket.object_versions.all().delete()
    bucket.delete()