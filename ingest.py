from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import boto3
import bucket
import generate_manifest
import iiif_jwt
import os

def wrapIngestRequest(
    metadata: dict,
    images: list,
    manifest: dict,
    spaceDefault: str,
    actionDefault: str = "upsert",
    ) -> dict:
    """Creates a JSON ingest request to be sent to the LTS MPS ingest API"""
    req = {
        "globalSettings" : {
            "actionDefault": actionDefault,
            "spaceDefault": spaceDefault
        },
        "metadata": metadata,
        "assets": {
            "audio": [],
            "video": [],
            "text": [],
            "image": images
        },
        manifest: manifest
    }
    return req

def createImageAsset(
    identifier: str,
    space: str,
    sourceSystemId: str,
    storageSrcPath: str,
    storageSrcKey: str,
    storageDestPath: str,
    storageDestKey: str,
    assetLocation: str,
    
    action: str = "create",
    createdByAgent: str = "???",
    lastModifiedByAgent: str = "???",
    createDate: datetime = datetime.now(ZoneInfo("America/New_York")),
    lastModifiedDate: datetime = datetime.now(ZoneInfo("America/New_York")),
    status: str = "ACTIVE",
    iiifApiVersion: int = 3,
    mediaType: str = "image",
    policyDefinition: dict = { "policyGroupName": "default"},
    assetMetadata: list = []
) -> dict:
    return {
        "action": action,
        "sourceSystemId": sourceSystemId,
        "storageSrcPath": storageSrcPath,
        "storageSrcKey": storageSrcKey,
        "storageDestPath": storageDestPath,
        "storageDestKey": storageDestKey,
        "identifier": identifier,
        "space": space,
        "createdByAgent": createdByAgent,
        "createDate": createDate,
        "lastModifiedByAgent": lastModifiedByAgent,
        "lastModifiedDate": lastModifiedDate,
        "status": status,
        "iiifApiVersion": iiifApiVersion,
        "assetLocation": assetLocation,
        "mediaType": mediaType,
        "policyDefinition": policyDefinition,
        "assetMetadata": assetMetadata
    }

def sendIngestRequest(
    req: dict,
    endpoint: str,
    token
):
    r = requests.post(
        endpoint,
        headers = {
            "Authorization": f"Bearer {token}"
        },
        data=req
    )
    return r

def ingestImages(
    images: list,
    issuer: str,
    manifest_level_metadata: dict,
    base_url: str, # what is this / is it generated?
    bucket_name: str, #find a better way to map all of these related things, eg given an issuer and environment I shouldn't need to remember the bucket
    spaceDefault: str, #same with this
    endpoint: str, #same with this
    environment: str = "qa",
    session=None,
    existing_manifest: dict = None
) -> bool:
    """Given an ordered list of dicts with filenames and metadata, upload images to S3,
    create a manifest, create a JWT, and kick off an ingest request"""
    # Example images
    # [
    #     {
    #         "label": "Canvas Title",
    #         "filepath": "/usr/media/myfile.jpg",
    #         "metadata": [
    #             {
    #                 "label": "Reference",
    #                 "value": "ID124",
    #                 "label_lang": "en",
    #                 "value_lang": "en"
    #             }
    #         ],
    #         "service": "/full/max/0/default.jpg",
    #         "id": "????"
    #     }
    # ]

    if not session:
        session = boto3._get_default_session()
    s3 = session.resource('s3')
    
    # Upload to S3
    for image in images:
        upload_response = bucket.upload_image_get_metadata(
            image_path=image.image_path,
            bucket_name=bucket_name,
            s3_path=image.s3_path,
            session=session)
        image["response"] = upload_response
    
    # Create manifest
    if not existing_manifest:
        canvases = []
        for image in images:
            canvas = {
                "label": image["label"],
                "width": image["response"]["width"],
                "height": image["response"]["height"],
                "id": image["id"],
                "service": image["service"],
                "metadata": image["metadata"]
            }
            canvases.append(canvas)
        manifest = generate_manifest.createManifest(
            base_url = base_url,
            labels = manifest_level_metadata["labels"],
            canvases = canvases,
            behaviors = manifest_level_metadata["behaviors"], #how to only pass if not None?
            rights = manifest_level_metadata["rights"], #same
            required_statement = manifest_level_metadata["required_statement"], #same
            manifestMetadata=manifest_level_metadata["metadata"] #same
        )
    else:
        manifest = existing_manifest

    # Create token
    iiif_jwt.load_auth(
        issuer=issuer,
        environement=environment
    )
    token = iiif_jwt.make_iiif_jwt(
        os.environ.get("ISSUER"),
        ["ingest"],
        os.environ.get("PRIVATE_KEY_PATH"),
        os.environ.get("KEY_ID")
    )

    # Create assets for ingest
    assets = []
    for image in images:
        asset = createImageAsset()
        assets.append(asset)
    
    #Create request
    request_body = wrapIngestRequest(
        images=assets,
        manifest=manifest,
        metadata={},
        spaceDefault=spaceDefault,
        actionDefault="upsert"
    )

    # Send request
    req = sendIngestRequest(
        req = request_body,
        endpoint = endpoint,
        token = token
    )

    #what should this return?