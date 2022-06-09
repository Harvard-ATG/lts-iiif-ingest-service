import os
import os.path

import boto3
import pytest

from IIIFingest.client import Client
from IIIFingest.auth import Credentials

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(TESTS_DIR, "images")


@pytest.fixture
def images_dir():
    """Directory of test images."""
    return IMAGES_DIR


@pytest.fixture
def test_images(images_dir):
    """Images available for testing."""
    return {
        "mcihtest1.tif": {
            "filepath": os.path.join(images_dir, "mcihtest1.tif"),
            "filename": "mcihtest1.tif",
            "format": "image/tiff",
            "width": 3600,
            "height": 584,
        },
        "mcihtest2.tif": {
            "filepath": os.path.join(images_dir, "mcihtest2.tif"),
            "filename": "mcihtest2.tif",
            "format": "image/tiff",
            "width": 3600,
            "height": 621,
        },
        "mcihtest3.tif": {
            "filepath": os.path.join(images_dir, "mcihtest3.tif"),
            "filename": "mcihtest3.tif",
            "format": "image/tiff",
            "width": 3600,
            "height": 621,
        },
        "27.586.1-cm-2016-02-09.tif": {
            "filepath": os.path.join(images_dir, "27.586.1-cm-2016-02-09.tif"),
            "filename": "27.586.1-cm-2016-02-09.tif",
            "format": "image/tiff",
            "width": 3600,
            "height": 564,
        },
        "27.586.126A-cm-2016-02-09.tif": {
            "filepath": os.path.join(images_dir, "27.586.126A-cm-2016-02-09.tif"),
            "filename": "27.586.126A-cm-2016-02-09.tif",
            "format": "image/tiff",
            "width": 3600,
            "height": 584,
        },
        "27.586.248A-cm-2016-02-09.tif": {
            "filepath": os.path.join(images_dir, "27.586.248A-cm-2016-02-09.tif"),
            "filename": "27.586.248A-cm-2016-02-09.tif",
            "format": "image/tiff",
            "width": 3600,
            "height": 621,
        },
        "27.586.249A-cm-2016-02-09.tif": {
            "filepath": os.path.join(images_dir, "27.586.249A-cm-2016-02-09.tif"),
            "filename": "27.586.249A-cm-2016-02-09.tif",
            "format": "image/tiff",
            "width": 3600,
            "height": 621,
        },
        "27.586.2A-cm-2016-02-09.tif": {
            "filepath": os.path.join(images_dir, "27.586.2A-cm-2016-02-09.tif"),
            "filename": "27.586.2A-cm-2016-02-09.tif",
            "format": "image/tiff",
            "width": 3600,
            "height": 581,
        },
    }


@pytest.fixture
def boto_session():
    """Fake boto session for testing."""
    return boto3.Session(
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        aws_session_token="testing",
        region_name='us-east-1',
    )


@pytest.fixture
def test_client(boto_session):
    issuer = ("atomeka_test",)
    kid = ("atomekadefault_test",)
    private_key_path = (os.path.join("./auth/test", "private.key"))
    test_jwt_cred = Credentials(
        issuer,
        kid,
        private_key_path=private_key_path,
    )
    client = Client(
        account="at",
        space="atomeka",
        namespace="at",
        environment="dev",
        asset_prefix="test",
        jwt_creds=test_jwt_cred,
        boto_session=boto_session,
    )

    return client
