# Will have functionality to kick off ingests
# Need to handle ingests with existing manifests or those that need to have manifests created
from datetime import datetime
from zoneinfo import ZoneInfo

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