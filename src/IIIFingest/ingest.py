from datetime import datetime
from socket import MsgFlag
from urllib import request
from zoneinfo import ZoneInfo
import requests
import boto3
from IIIFingest.bucket import upload_image_get_metadata
import generate_manifest
import os
import shortuuid
import mimetypes
import json
from PIL import Image
from IIIFingest.iiif_jwt import Credentials
from IIIFingest.settings import ROOT_DIR
import time
# import threading

class IIIFCanvas:
    def __init__(
        self,
        filepath: str, # Do we need this? Or can we get away with just having path_filename? In a cloud environment probably won't have a local reference
        width: int,
        height: int,
        asset_id: str = None, # Alphanumeric only. If None, it is generated. Asset_app_prefix (eg MCIH) + path_filename (eg /test_images/mcihtest1.tif = mcihtest) + uuid if add_uuid, eg AT:MCIHmcihtest1Dj73bjEbHfjwXBoLH5MWgm
        add_uuid: bool = False,
        asset_app_prefix: str = "", # eg "MCIH" - only alphanumeric, can't use other seps like ":"
        label: str = None, # If None, it is set to the asset_id
        mps_base: str = "https://mps-qa.lib.harvard.edu/assets/images/AT:",
        service: str = None, # Eg /full/max/0/default.jpg
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
            asset_str += f"{shortuuid.uuid()}"
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

# For consistency, either imageAsset should also be a class, or turn IIIFCanvas into a method which wraps dict properties
# Currently, generate_manifest expects a list of dicts
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
    """Creates an ingest request to be sent to the LTS MPS ingest API"""
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
) -> request:
    r = requests.post(
        endpoint,
        headers = {
            "Authorization": f"Bearer {token}"
        },
        json=req
    )
    return r

def jobStatus(
    job_id: str,
    endpoint: str = "https://mps-admin-qa.lib.harvard.edu/admin/ingest/jobstatus/"
) -> request:
    url = f"{endpoint}{job_id}"
    r = requests.get(
        url
    )
    return r

def pingJob(
    job_id: str,
    endpoint: str = "https://mps-admin-qa.lib.harvard.edu/admin/ingest/jobstatus/",
    max_pings: int = 25,
    interval: int = 10,
    print_status = True
) -> dict:
    working = True
    completed = False
    start = time.time()
    pings = 0
    while working:
        pings += 1
        r = jobStatus(job_id, endpoint)
        status = r.json()
        end = time.time()
        msg = ""
        if(status["data"].get("job_status") == "success"):
            msg = f"------- Job {job_id} finished ingesting after {round(end - start)} seconds and {pings} pings -------"
            if(print_status):
                print(msg)
                print(status)
            completed = True
            working = False
        elif(status["data"].get("job_status") == "running"):
            msg = f"-------- Job {job_id} processing. {round(end - start)} seconds and {pings} pings -------"
            if(print_status):
                print(msg)
                print(status)
            time.sleep(interval)
        elif(status["data"].get("job_status") == "failed"):
            msg = f"-------- Job {job_id} Failed. {round(end - start)} seconds and {pings} pings -------"
            if(print_status):
                print(msg)
                print(status)
            working = False
        elif(pings > max_pings):
            msg = f"-------- Job {job_id} did not complete within {round(end - start)} seconds and {pings} pings (max pings {max_pings})"
            if(print_status):
                print(status)
            working=False
        else:
            msg = f"-------- Job {job_id} delivered an invalid status. {round(end - start)} seconds and {pings} pings -------"
            if(print_status):
                print(status)
            working = False
    
    return {
        "completed": completed,
        "message": msg,
        "job_id": job_id,
        "endpoint": endpoint,
        "pings": pings,
        "elapsed": round(time.time() - start)
    }


def ingestImages(
    image_dicts: list,
    issuer: str, #e.g. "atmch", "atmediamanager", "atomeka", "atdarth"
    jwt_creds: Credentials, # Credentials class from iiif_jwt
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
    add_uuid = True,
    track_job_status = False,
    job_endpoint: str = "https://mps-admin-qa.lib.harvard.edu/admin/ingest/jobstatus/",
    print_job_status = False,
    max_job_pings: int = 25,
    job_ping_interval: int = 10,
) -> dict:
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

        s3key = upload_image_get_metadata(
            image_path=image.get("filepath"),
            bucket_name=bucket_name,
            s3_path=s3_path,
            session=session
        )
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
            image["IIIFCanvas"] = image_dict # this is a bit messy. Maybe only keep these properties in one place rather than in "images" and "canvases"? Right now all canvases only have 1 image
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

        # print("------ test manifest ------")
        # manifest.inspect()
    else:
        manifest = existing_manifest

    # Create token
    token = jwt_creds.make_jwt()

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
    print("---- r -----")
    print(r.text)
    response_dict = json.loads(r.text)
    print(json.dumps(response_dict, indent=4, sort_keys=True))
    
    #what should this return? The job id should be in the response, use that and the endpoint to check on status
    if not track_job_status:
        return {
            "tracking": False,
            "job_status": "Unknown - not tracking",
            "ingest_request": r.json(),
            "manifest_url": manifest.id
        }
    else:
        #track the job
        ingest_request = r.json()
        job_id = ingest_request["data"]["job_tracker_file"].get("_id", None)
        if not job_id:
            print("Job not found. Maybe the ingest request failed?")
            print("Dumping response")
            print(r.json())
            return {
                "tracking": True,
                "completed": False,
                "ingest_request": r.json(),
                "manifest_url": manifest.id,
                "job_status": "Unknown - job not found"
            }
        else:
            status = pingJob(
                job_id=job_id,
                endpoint=job_endpoint,
                max_pings=max_job_pings,
                interval=job_ping_interval,
                print_status=print_job_status
            )
            if(status.get("completed")):
                print(f"Manifest {manifest.id} now available")
                result = {
                    "tracking": True,
                    "completed": status.get("completed"),
                    "ingest_request": r.json(),
                    "manifest_url": manifest.id,
                    "job_id": job_id,
                    "job_status": status
                }
                print(result)
                return result
            else:
                print("Job failed or did not complete in the allotted timeframe")
                result = {
                    "tracking": True,
                    "completed": status.get("completed"),
                    "ingest_request": r.json(),
                    "manifest_url": manifest.id,
                    "job_id": job_id,
                    "job_status": status
                }
                print(result)
                return result


def test_ingest_pipeline() -> None:
    # QA environment - DARTH keys and buckets for testing
    darth_qa_session = boto3.Session(profile_name='mps-darth-qa')

    # or, pass the keys if named profiles aren't available
    # darth_qa_session = boto3.Session(
    #     aws_access_key_id=ACCESS_KEY,
    #     aws_secret_access_key=SECRET_KEY,
    ##     aws_session_token=SESSION_TOKEN # only needed if using temporary credentials
    # )

    creds = Credentials(
        issuer="atdarth",
        kid="atdarthdefault",
        private_key_path=os.path.join(ROOT_DIR, f"auth/qa/keys/atdarth/atdarthdefault/private.key")
    )
    
    images = [
        {
            "label": "27.586.126A",
            "filepath": "../tests/test_images/mcihtest1.tif",
        },
        {
            "label": "27.586.248A",
            "filepath": "../tests/test_images/mcihtest2.tif",
            "metadata": [
                {
                    "label": "Test",
                    "value": "Image level metadata"
                }
            ]
        },
        {
            "label": "27.586.249A",
            "filepath": "../tests/test_images/mcihtest3.tif"
        }
    ]
    ingestImages(
        image_dicts=images,
        issuer="atdarth",
        session = darth_qa_session,
        jwt_creds = creds,
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
        asset_app_prefix="MCIH",
        track_job_status=True,
        job_endpoint = "https://mps-admin-qa.lib.harvard.edu/admin/ingest/jobstatus/",
        print_job_status=True
    )

if __name__ == '__main__':
    test_ingest_pipeline()