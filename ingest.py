from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import boto3
import bucket
import generate_manifest
import iiif_jwt
import os
import shortuuid
import mimetypes
import json
from PIL import Image

class IIIFCanvas:
    def __init__(
        self,
        filepath: str,
        width: int,
        height: int,
        asset_id: str = None, #recommended
        add_uuid: bool = False,
        asset_app_prefix: str = "", # "MCIH:"
        label: str = None,
        mps_base: str = "https://mps-qa.lib.harvard.edu/assets/images/AT:",
        service: str = None,
        format: str = None,
        metadata: list = None
    ):
        self.filepath = filepath
        path_root, extension = os.path.splitext(filepath)
        path_filename = os.path.basename(path_root)
        print(f"IIIFCanvas - {self.filepath} | {path_filename} | {extension}")
        self.width = width
        self.height = height

        asset_id = asset_id or path_filename #check to see if this works correctly
        asset_str = f"{asset_app_prefix}{asset_id}"
        if(add_uuid):
            asset_str += f":{shortuuid.uuid()}"
        self.asset_id = asset_str
        self.label = label or self.asset_id
        mps_base = mps_base or "https://mps-qa.lib.harvard.edu/assets/images/AT:"
        self.id = f"{mps_base}{self.asset_id}"

        self.format = format or mimetypes.guess_type(filepath)
        self.service = service or f"/full/max/0/default{extension}"
        self.metadata = metadata
    
    def toDict(self):
        return dict(
            filepath=self.filepath,
            width=self.width,
            height=self.height,
            asset_id=self.asset_id,
            label = self.label,
            id = self.id,
            format = self.format,
            service = self.service,
            metadata = self.metadata
        )

def createImageAsset(
    identifier: str,
    space: str,
    storageSrcPath: str,
    storageSrcKey: str,
    
    action: str = "create",
    createdByAgent: str = "atagent",
    lastModifiedByAgent: str = "atagent",
    createDate: str = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S"),
    lastModifiedDate: str = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S"),
    status: str = "ACTIVE",
    iiifApiVersion: str = "3",
    policyDefinition: dict = { "policyGroupName": "default"},
    assetMetadata: list = []
) -> dict:
    return {
        "action": action,
        "storageSrcPath": storageSrcPath,
        "storageSrcKey": storageSrcKey,
        "identifier": identifier,
        "space": space,
        "createdByAgent": createdByAgent,
        "createDate": createDate,
        "lastModifiedByAgent": lastModifiedByAgent,
        "lastModifiedDate": lastModifiedDate,
        "status": status,
        "iiifApiVersion": iiifApiVersion,
        "policyDefinition": policyDefinition,
        "assetMetadata": assetMetadata
    }

def wrapIngestRequest(
    metadata: dict,
    assets: list,
    manifest: dict,
    space_default: str,
    action_default: str = "upsert",
    ) -> dict:
    """Creates a JSON ingest request to be sent to the LTS MPS ingest API"""
    req = {
        "globalSettings" : {
            "actionDefault": action_default,
            "spaceDefault": space_default
        },
        "metadata": metadata,
        "assets": {
            "audio": [],
            "video": [],
            "text": [],
            "image": assets
        },
        "manifest": manifest
    }
    return req


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
        json=req
    )
    return r

def ingestImages(
    image_dicts: list,
    issuer: str, #e.g. "atmch", "atmediamanager", "atomeka", "atdarth"
    manifest_level_metadata: dict,
    base_url: str, #e.g. https://nrs-qa.lib.harvard.edu/URN-3:AT:TESTMANIFEST3:MANIFEST:3 - URN-3:{namespace}:{manifestname}:MANIFEST:{PreziVersion}
    bucket_name: str, #find a better way to map all of these related things, eg given an issuer and environment I shouldn't need to remember the bucket
    space_default: str, #same with this
    endpoint: str, #same with this
    s3_path: str = "",
    environment: str = "qa",
    asset_app_prefix: str = None,
    mps_base: str = None,
    session=None,
    existing_manifest: dict = None,
    add_uuid = True
) -> bool:
    """Given an ordered list of dicts with filenames and metadata, upload images to S3,
    create a manifest, create a JWT, and kick off an ingest request"""

    if not session:
        session = boto3._get_default_session()
    s3 = session.resource('s3')
    
    # Upload to S3
    for image in image_dicts:
        # get the image metadata
        img = Image.open(image.get("filepath"))
        width, height = img.size
        format = img.get_format_mimetype()

        s3key = bucket.upload_image_get_metadata(
            image_path=image.get("filepath"),
            bucket_name=bucket_name,
            s3_path=s3_path,
            session=session)
        image["s3key"] = s3key
        image["width"] = width
        image["height"] = height
        image["format"] = format
        print(image)
    
    # Create manifest
    if not existing_manifest:
        print("Creating manifests")
        canvases = []
        for image in image_dicts:
            # Create canvases
            canvas = IIIFCanvas(
                filepath=image.get("filepath"),
                width=image.get("width"),
                height=image.get("height"),
                asset_id=image.get("asset_id", None),
                add_uuid=add_uuid,
                asset_app_prefix=asset_app_prefix or "",
                label=image.get("label"),
                format=image.get("format", None),
                metadata=image.get("metadata", []),
                mps_base = mps_base or None,
                service = image.get("service", None)
            )
            image_dict = canvas.toDict()
            print("image dict")
            print(image_dict)
            canvases.append(image_dict) # pass as dicts, because generate_manifest is currently expecting a list of dicts, not list of IIIFCanvases
            image["IIIFCanvas"] = image_dict
            print("image")
            print(image)
            
        manifest_kwargs=dict(
            base_url = base_url,
            labels = manifest_level_metadata["labels"],
            canvases = canvases,

            behaviors = manifest_level_metadata.get("behaviors", None),
            providers = manifest_level_metadata.get("providers", None),
            rights = manifest_level_metadata.get("rights", None),
            required_statement = manifest_level_metadata.get("required_statement", None),
            manifest_metadata=manifest_level_metadata.get("metadata", None),
            default_lang=manifest_level_metadata.get("default_lang", None), #need to add this?
            namespace_prefix=manifest_level_metadata.get("namespace_prefix", None), # need to add this?
            service_type=manifest_level_metadata.get("service_type", None), #need to add this ?
            service_profile=manifest_level_metadata.get("service_profile", None) #need to add this
        )
        # pass only args which are not None, so we can use the createManifest defaults
        manifest = generate_manifest.createManifest(**{k: v for k, v in manifest_kwargs.items() if v is not None})
        print("------ Manifest ------")
        print(type(manifest))
        print(manifest)

        print("------ test manifest ------")
        # manifest.inspect()
    else:
        manifest = existing_manifest

    # Create token
    iiif_jwt.load_auth(
        issuer=issuer,
        environment=environment
    )
    token = iiif_jwt.make_iiif_jwt(
        os.environ.get("ISSUER"),
        ["ingest"],
        os.environ.get("PRIVATE_KEY_PATH"),
        os.environ.get("KEY_ID")
    )
    print(token)

    # Create assets for ingest
    assets = []
    for image in image_dicts:
        file_dir, file_name = os.path.split(image.get("filepath"))
        asset = createImageAsset(
            identifier = f"{manifest_level_metadata.get('namespace_prefix')}:{image.get('IIIFCanvas').get('asset_id')}",
            space = image.get("space", space_default),
            storageSrcPath = s3_path,
            storageSrcKey = file_name
            # handle other params later?
        )
        assets.append(asset)
    print(assets)
    
    #Create request
    request_body = wrapIngestRequest(
        assets=assets,
        manifest=json.loads(manifest.json_dumps()),
        metadata={},
        space_default=space_default,
        action_default="upsert"
    )
    print("request_body --------------------")
    print(request_body)

    # Send request
    r = sendIngestRequest(
        req = request_body,
        endpoint = endpoint,
        token = token
    )
    response_dict = json.loads(r.text)
    print(json.dumps(response_dict, indent=4, sort_keys=True))
    
    #what should this return? The job id should be in the response, use that and the endpoint to check on status
    return r        

def test_ingest_pipeline():
    
    images = [
        {
            "label": "27.586.126A",
            "filepath": "./test_images/27.586.126A-cm-2016-02-09.tif",
        },
        {
            "label": "27.586.248A",
            "filepath": "./test_images/27.586.248A-cm-2016-02-09.tif",
            "metadata": [
                {
                    "label": "Test",
                    "value": "Image level metadata"
                }
            ]
        },
        {
            "label": "27.586.249A",
            "filepath": "./test_images/27.586.249A-cm-2016-02-09.tif"
        }
    ]
    ingestImages(
        image_dicts=images,
        issuer="atdarth",
        manifest_level_metadata=dict(
            labels=[
                "Test Manifest MCIH"
            ],
            metadata=[
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
            required_statement=[
                {
                    "label": "Attribution",
                    "value": "Jinah Kim"
                }
            ],
            default_lang="en",
            namespace_prefix="AT",
            service_type="ImageService2",
            service_profile="level2",
            rights="http://creativecommons.org/licenses/by-sa/3.0/",
            summary="A test manifest for Mapping Color in History ingest into MPS IIIF delivery solution",
            providers = [
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
        ),
        base_url=f"https://nrs-qa.lib.harvard.edu/URN-3:AT:TEST{shortuuid.uuid()}:MANIFEST:3",
        bucket_name="edu.harvard.huit.lts.mps.at-atdarth-qa",
        s3_path = "mcih/",
        space_default="atdarth",
        endpoint="https://mps-admin-qa.lib.harvard.edu/admin/ingest/initialize",
        environment="qa",
        asset_app_prefix="MCIH:"
    )

if __name__ == '__main__':
    test_ingest_pipeline()