import os
import os.path

import pytest

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


@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
