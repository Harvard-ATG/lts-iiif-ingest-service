import sys
import os
import boto3
import logging

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT_DIR, 'src'))
print(sys.path)

from IIIFingest.client import Client
from IIIFingest.iiif_jwt import Credentials

## Configure logging
root = logging.getLogger()
root.setLevel(logging.INFO)

pkg = logging.getLogger('IIIFingest')
pkg.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

## Client configuration
asset_prefix = "mcih"
issuer = "atmediamanager"
space = "atmediamanager"
environment = "qa"
session = boto3.Session(profile_name=f"mps-{space}-{environment}")

jwt_creds = Credentials(
    issuer=issuer,
    kid=f"{issuer}default",
    private_key_path=os.path.join(ROOT_DIR, f"auth/{environment}/keys/{issuer}/{issuer}default/private.key"),
)

client = Client(
    space=space,
    environment=environment,
    asset_prefix=asset_prefix,
    jwt_creds=jwt_creds,
    boto_session=session,
)

images = [
    {
        "label": "27.586.126A",
        "filepath": os.path.join(ROOT_DIR, "src/tests/test_images/mcihtest1.tif"),
    },
    # {
    #     "label": "27.586.248A",
    #     "filepath": os.path.join(ROOT_DIR, "src/tests/test_images/mcihtest2.tif"),
    #     "metadata": [
    #         {
    #             "label": "Test",
    #             "value": "Image level metadata"
    #         }
    #     ]
    # },
    # {
    #     "label": "27.586.249A",
    #     "filepath": os.path.join(ROOT_DIR, "src/tests/test_images/mcihtest3.tif"),
    # }
]

manifest_level_metadata={
    "labels": [
        "Test Manifest MCIH"
    ],
    "metadata": [
        {
            "label": "Creator",
            "value": "Unknown",
            "label_lang": "en",
            "value_lang": "en"
        },
        {
            "label": "Date",
            "value": "19th Century",
            "label_lang": "en",
            "value_lang": "en"
        }
    ],
    "required_statement": [
        {
            "label": "Attribution",
            "value": "Jinah Kim"
        }
    ],
    "default_lang": "en",
    "service_type": "ImageService2",
    "service_profile":"level2",
    "rights":"http://creativecommons.org/licenses/by-sa/3.0/",
    "summary":"A test manifest for Mapping Color in History ingest into MPS IIIF delivery solution",
    "providers": [
        {
            "labels": [
                {
                    "lang": "en",
                    "value": "Harvard University - Arts and Humanities Research Computing (organizing org)"
                }
            ],
            "id": "http://id.loc.gov/authorities/names/n78096930"
        },
        {
            "labels": [
                {
                    "value": "Harvard Art Museum (providing org)"
                }
            ],
            "id": "http://id.loc.gov/authorities/names/no2008065752"
        }
    ]
}

assets = client.upload(images=images, s3_path="images/")

manifest = client.create_manifest(
    manifest_level_metadata=manifest_level_metadata, 
    assets=assets,
)

result = client.ingest(
    assets=assets,
    manifest=manifest,
)

status = client.jobstatus(result["job_id"])
