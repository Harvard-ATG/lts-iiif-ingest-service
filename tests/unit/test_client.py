from email.policy import default
import os.path

import boto3
import jwt
import pytest

# from boto3.exceptions import S3UploadFailedError
# from botocore.exceptions import ClientError
from moto import mock_s3
from dotenv import load_dotenv

import re

from ...src.IIIFingest.client import Client
from ...src.IIIFingest.auth import Credentials
from ...src.IIIFingest.settings import ROOT_DIR

load_dotenv()

abs_path = os.path.abspath(os.path.join(ROOT_DIR, '../..'))
image_path = os.path.join(abs_path, "images", "27.586.1-cm-2016-02-09.tif")
private_key_path = os.path.join(abs_path, "auth/dev/omeka", "private.key")


@mock_s3
class TestClient:
    test_aws_profile = os.getenv('TEST_AWS_PROFILE')
    bucket_name = os.getenv('TEST_BUCKET')
    default_session = boto3.Session(profile_name=test_aws_profile)

    @pytest.fixture(autouse=True, scope='class')
    def setup_conn(self):
        self.__class__.conn = boto3.resource('s3', region_name='us-east-1')

    # Configure ingest API auth credentials
    jwt_creds = Credentials(
        issuer="atomeka",
        kid="atomekadefault",
        private_key_path=private_key_path,
    )

    client = Client(
        account="ataccount",
        space="atspace",
        namespace="at",
        environment="dev",
        asset_prefix="myapp",
        jwt_creds=jwt_creds,
        boto_session=default_session,
    )

    # Define images to ingest
    images = [{"label": "Test Image", "filepath": image_path}]

    # Define manifest-level metadata
    manifest_level_metadata = {
        "labels": ["Test Manifest"],
        "summary": "A test manifest for ingest",
        "rights": "http://creativecommons.org/licenses/by-sa/3.0/",
    }

    def test_client_upload(self):
        self.conn.create_bucket(Bucket=self.bucket_name)
        jwt_creds = Credentials(
            issuer="atomeka", kid="atomekadefault", private_key_path=private_key_path
        )
        #TODO move to fixture
        # Add failing test as well
        client = Client(
            account="at",
            space="atomeka",
            namespace="at",
            environment="dev",
            asset_prefix="test",
            jwt_creds=jwt_creds,
            boto_session=self.default_session,
        )

        images = [{"label": "Test Image", "filepath": image_path}]
        assets = client.upload(images, s3_path="testing")

        assert assets is not None
        assert assets[0].filepath == image_path


    def test_client_create_manifest(self):
        self.conn.create_bucket(Bucket=self.bucket_name)
        jwt_creds = Credentials(
            issuer="atomeka", kid="atomekadefault", private_key_path=private_key_path
        )

        client = Client(
            account="at",
            space="atomeka",
            namespace="at",
            environment="dev",
            asset_prefix="test",
            jwt_creds=jwt_creds,
            boto_session=self.default_session,
        )

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
        item =  manifest["items"][0]
        # TODO could add test to test for all properties to make sure they are generated correctly? 
        assert len(manifest["items"]) == 1
        assert matches_root_id is not None
        assert item["height"] == 564 and item["width"] == 3600
