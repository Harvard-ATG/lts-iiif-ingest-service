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
        path_filename, extension = os.path.splitext(filepath)
        self.width = width
        self.height = height

        asset_id = asset_id or path_filename #check to see if this works correctly
        asset_str = f"{asset_app_prefix}{asset_id}"
        if(add_uuid):
            asset_str += f":{shortuuid.uuid()}"
        self.asset_id = asset_str
        self.label = label or self.asset_id
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
    createDate: datetime = datetime.now(ZoneInfo("America/New_York")),
    lastModifiedDate: datetime = datetime.now(ZoneInfo("America/New_York")),
    status: str = "ACTIVE",
    iiifApiVersion: int = 3,
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
        manifest: manifest
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
        data=req
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
    # Example images
    # [
    #     {
    #         "label": "Canvas Title",
    #         "filepath": "/usr/media/myfile.jpg", #LOCAL
    #         "metadata": [
    #             {
    #                 "label": "Reference",
    #                 "value": "ID124",
    #                 "label_lang": "en",
    #                 "value_lang": "en"
    #             }
    #         ],
    #         "service": "/full/max/0/default.jpg",
    #         "id": "https://mps-qa.lib.harvard.edu/assets/images/AT:TESTASSET3" 
    #     }
    # ]

    if not session:
        session = boto3._get_default_session()
    s3 = session.resource('s3')
    
    # Upload to S3
    for image in image_dicts:
        # get the image metadata
        # TODO finish this - functionality moved from bucket; the bucket shouldn't need to return anything besides the s3key
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
    
    # Create manifest
    if not existing_manifest:
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
                format = image.get("format", None),
                service = image.get("service", None)
            )
            canvases.append(canvas.toDict) # pass as dicts, because generate_manifest is currently expecting a list of dicts, not list of IIIFCanvases
        manifest_kwargs=dict(
            base_url = base_url,
            labels = manifest_level_metadata["labels"],
            canvases = canvases,

            behaviors = manifest_level_metadata.get("behaviors", None),
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

    # Create assets for ingest
    assets = []
    for image in image_dicts:
        file_dir, file_name = os.path.split(image.get("filepath"))
        asset = createImageAsset(
            identifier = "???",
            space = image.get("space", space_default),
            storageSrcPath = s3_path,
            storageSrcKey = file_name
            # handle other params later?
        )
        assets.append(asset)
    
    #Create request
    request_body = wrapIngestRequest(
        assets=assets,
        manifest=manifest,
        metadata={},
        space_default=space_default,
        action_default="upsert"
    )

    # Send request
    r = sendIngestRequest(
        req = request_body,
        endpoint = endpoint,
        token = token
    )
    
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
        images=images,
        issuer="atdarth",
        manifest_level_metadata=dict(
            labels=[],
            metadata=[],
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
            rights="http://creativecommons.org/licenses/by-sa/3.0/"
        ),
        base_url="",
        bucket_name="",
        space_default="atdarth",
        endpoint="",
        environment="qa"
    )

if __name__ == '__main__':
    test_ingest_pipeline()


                base_url = base_url,
            labels = manifest_level_metadata["labels"],
            canvases = canvases,

            behaviors = manifest_level_metadata.get("behaviors", None),
            rights = manifest_level_metadata.get("rights", None),
            required_statement = manifest_level_metadata.get("required_statement", None),
            manifest_metadata=manifest_level_metadata.get("metadata", None),
            default_lang=manifest_level_metadata.get("default_lang", None), #need to add this?
            namespace_prefix=manifest_level_metadata.get("namespace_prefix", None), # need to add this?
            service_type=manifest_level_metadata.get("service_type", None), #need to add this ?
            service_profile=manifest_level_metadata.get("service_profile", None) #need to add this