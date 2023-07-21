from email.policy import default
import os.path

import boto3
import jwt
import pytest
# from boto3.exceptions import S3UploadFailedError
# from botocore.exceptions import ClientError
from moto import mock_s3
from dotenv import load_dotenv

from ...client import Client
from ...auth import Credentials
from ...settings import ROOT_DIR

load_dotenv()

abs_path = os.path.abspath(os.path.join(ROOT_DIR, '../..'))
image_name = "27.586.1-cm-2016-02-09.tif"
image_path = os.path.join(abs_path, "images", image_name)
private_key_path = os.path.join(abs_path, "auth/dev/omeka","private.key")

class TestClient:
    test_aws_profile = os.getenv('TEST_AWS_PROFILE')
    bucket_name = os.getenv('TEST_BUCKET')
    default_session = boto3.Session(profile_name=test_aws_profile)
    def setup_conn(self):
        self.__class__.conn = boto3.resource('s3', region_name='us-east-1')
    # Configure ingest API auth credentials
    jwt_creds = Credentials(
        issuer="atomeka",
        kid="atomekadefault",
        # private_key_string=private_key_string,
        private_key_path=private_key_path
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
    images = [{
        "label": "Test Image", 
        "filepath": image_path
    }]

    # Define manifest-level metadata
    manifest_level_metadata = {
        "labels": ["Test Manifest"],
        "summary": "A test manifest for ingest",
        "rights": "http://creativecommons.org/licenses/by-sa/3.0/",
    }

    # Call client methods as needed
    def test_client_upload(self):
        # self.conn.create_bucket(Bucket=self.bucket_name)
        # assert private_key_string == ""
        jwt_creds = Credentials(
        issuer="atomeka",
        kid="atomekadefault",
        private_key_path=private_key_path
        )

        # Define images to ingest
        # images = [{
        #     "label": "Test Image", 
        #     "filepath": image_path
        # }]

        client = Client(
            account="at",
            space="atomeka",
            namespace="at",
            environment="dev",
            asset_prefix="test",
            jwt_creds=jwt_creds,
            boto_session=self.default_session,
        )


        manifest_level_metadata = {
        "labels": ["Test Manifest"],
        "summary": "A test manifest for ingest",
        "rights": "http://creativecommons.org/licenses/by-sa/3.0/",
        }
        

        images = [{
        "label": "Test Image", 
        "filepath": image_path
        }]
        assets = client.upload(images, s3_path="testing")
        # assert assets == "fake"
        # s3 = self.default_session.client('s3')
        # s3.delete_object(Bucket=self.bucket_name, Key=f"testing/{image_name}")
        # for a in assets:
        #     assert a.to_dict() == ''

        # manifest = client.create_manifest(manifest_level_metadata=manifest_level_metadata, assets=assets)
        # assert jwt_creds.make_jwt() == ""
        # assets = self.client.upload(self.images)
        # assert assets == "test"

        manifest = client.create_manifest(manifest_level_metadata=manifest_level_metadata, assets=assets, manifest_name="functional_test")
        # print(manifest)
        result = client.ingest(manifest=manifest, assets=assets)
        status = client.jobstatus(result["job_id"])

        print("result", result)
        print("status", status)