import os.path

import pytest
from botocore.exceptions import ClientError
from moto import mock_s3

from IIIFingest.settings import MPS_ASSET_BASE_URL, MPS_MANIFEST_BASE_URL


@mock_s3
class TestClient:
    test_aws_profile = os.getenv('TEST_AWS_PROFILE', default="tester")
    # must match client params e.g. account space and environment - see conftest.py
    bucket_name = os.getenv(
        'TEST_BUCKET', default="edu.harvard.huit.lts.mps.test-testing-space-dev"
    )
    environment = "dev"
    namespace = "TEST"
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

        image_dict = assets[0]
        # assert image_dict.filepath == image_path
        assert image_dict.asset_id is not None
        assert image_dict.label == "Test Image"

    def test_client_upload_generate_asset_id(
        self, test_images, boto_session, test_client
    ):
        boto_session.resource('s3').create_bucket(Bucket=self.bucket_name)

        image_path = test_images["27.586.1-cm-2016-02-09.tif"]["filepath"]

        client = test_client
        test_image_id = "id123"
        images = [{"label": "Test Image", "filepath": image_path, "id": test_image_id}]
        assets = client.upload(images, s3_path="testing")

        assert assets is not None

        image_dict = assets[0]
        assert image_dict.filepath == image_path
        assert image_dict.asset_id.startswith(client.asset_prefix + test_image_id)
        assert image_dict.label == "Test Image"

    def test_client_upload_existing_asset_id(
        self, test_images, boto_session, test_client
    ):
        boto_session.resource('s3').create_bucket(Bucket=self.bucket_name)

        image_path = test_images["27.586.1-cm-2016-02-09.tif"]["filepath"]

        client = test_client
        test_image_id = "id123"
        asset_id = "mcih235dad6f-d157-42bc-91d1-67cbd59c7756".replace("-", "")
        images = [
            {
                "label": "Test Image",
                "filepath": image_path,
                "id": test_image_id,
                "asset_id": asset_id,
            }
        ]
        assets = client.upload(images, s3_path="testing")

        assert assets is not None

        image_dict = assets[0]
        assert image_dict.asset_id == asset_id
        assert image_dict.label == "Test Image"

    def test_client_upload_no_uuid(self, test_images, boto_session, test_client):
        boto_session.resource('s3').create_bucket(Bucket=self.bucket_name)

        image_path = test_images["27.586.1-cm-2016-02-09.tif"]["filepath"]

        client = test_client
        test_image_id = "id123"
        images = [{"label": "Test Image", "filepath": image_path, "id": test_image_id}]
        assets = client.upload(images, s3_path="testing", with_uuid=False)
        assert assets is not None

        image_dict = assets[0]
        assert image_dict.asset_id == f"{client.asset_prefix}{test_image_id}"
        assert image_dict.label == "Test Image"

    def test_client_fail_upload_non_alphanumeric_asset_id(
        self, test_images, boto_session, test_client
    ):
        boto_session.resource('s3').create_bucket(Bucket=self.bucket_name)

        image_path = test_images["27.586.1-cm-2016-02-09.tif"]["filepath"]

        client = test_client
        test_image_id = "id_123"
        images = [{"label": "Test Image", "filepath": image_path, "id": test_image_id}]
        with pytest.raises(ValueError):
            assert client.upload(images, s3_path="testing")

    def test_client_fail_upload_nonexistent_bucket(
        self, test_images, boto_session, test_client
    ):
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
        manually_created_base_manifest_url = MPS_MANIFEST_BASE_URL.format(
            environment=self.environment, namespace=self.namespace
        )
        manually_created_base_asset_url = MPS_ASSET_BASE_URL.format(
            environment=self.environment, namespace=self.namespace
        )
        manifest = client.create_manifest(
            manifest_level_metadata=self.manifest_level_metadata, assets=assets
        )
        manually_created_service = "/full/max/0/default" + assets[0].extension
        item = manifest["items"][0]
        assert len(manifest["items"]) == 1
        assert item["height"] == 564 and item["width"] == 3600
        assert manifest["id"].startswith(manually_created_base_manifest_url)
        # Test base asset url is correctly created
        manifest_body = item["items"][0]["items"][0]["body"]
        assert manifest_body["id"].endswith(manually_created_service)
        assert manifest_body["id"].startswith(manually_created_base_asset_url)
        assert manifest_body["format"] == assets[0].format

    def test_client_fail_create_manifest_missing_asset(self, boto_session, test_client):
        with pytest.raises(TypeError):

            boto_session.resource('s3').create_bucket(Bucket=self.bucket_name)
            client = test_client
            assert client.create_manifest(
                manifest_level_metadata=self.manifest_level_metadata,
            )

    def test_client_fail_create_manifest_missing_metadata(
        self, test_images, boto_session, test_client
    ):
        with pytest.raises(TypeError):

            boto_session.resource('s3').create_bucket(Bucket=self.bucket_name)
            client = test_client
            image_path = test_images["27.586.1-cm-2016-02-09.tif"]["filepath"]
            images = [{"label": "Test Image", "filepath": image_path}]
            assets = client.upload(images, s3_path="testing")
            assert client.create_manifest(assets=assets)
