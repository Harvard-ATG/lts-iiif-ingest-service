import logging
import time
from datetime import datetime
from urllib import request

import requests

# Backports supports Python 3.6-3.8
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


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
    createDate: str = datetime.now(ZoneInfo("America/New_York")).strftime(
        "%Y-%m-%d %H:%M:%S"
    ),
    lastModifiedDate: str = datetime.now(ZoneInfo("America/New_York")).strftime(
        "%Y-%m-%d %H:%M:%S"
    ),
    status: str = "ACTIVE",
    iiifApiVersion: str = "3",
    policyDefinition: dict = {"policyGroupName": "default"},
    assetMetadata: list = [],
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
        "assetMetadata": assetMetadata,
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
        "globalSettings": {
            "actionDefault": action_default,
            "spaceDefault": space_default,
        },
        "metadata": metadata,
        "assets": {"audio": [], "video": [], "text": [], "image": assets},
        "manifest": manifest,
    }
    return req


def sendIngestRequest(req: dict, endpoint: str, token) -> request:
    r = requests.post(endpoint, headers={"Authorization": f"Bearer {token}"}, json=req)
    return r


def jobStatus(
    job_id: str,
    endpoint: str = "https://mps-admin-qa.lib.harvard.edu/admin/ingest/jobstatus/",
) -> request:
    url = f"{endpoint}{job_id}"
    r = requests.get(url)
    return r


def pingJob(
    job_id: str,
    endpoint: str = "https://mps-admin-qa.lib.harvard.edu/admin/ingest/jobstatus/",
    max_pings: int = 25,
    interval: int = 10,
) -> dict:
    working = True
    completed = False
    start = time.time()
    pings = 0
    status = {}
    while working:
        pings += 1
        r = jobStatus(job_id, endpoint)
        status = r.json()
        end = time.time()
        msg = ""
        if status["data"].get("job_status") == "success":
            msg = f"------- Job {job_id} finished ingesting after {round(end - start)} seconds and {pings} pings -------"
            logger.debug(msg)
            logger.debug(status)
            completed = True
            working = False
        elif status["data"].get("job_status") == "running":
            msg = f"-------- Job {job_id} processing. {round(end - start)} seconds and {pings} pings -------"
            logger.debug(msg)
            logger.debug(status)
            time.sleep(interval)
        elif status["data"].get("job_status") == "failed":
            msg = f"-------- Job {job_id} Failed. {round(end - start)} seconds and {pings} pings -------"
            logger.debug(msg)
            logger.debug(status)
            working = False
        elif status["data"].get("job_status") == "queued":
            msg = f"-------- Job {job_id} queued. {round(end - start)} seconds and {pings} pings -------"
            logger.debug(msg)
            logger.debug(status)
            time.sleep(interval)
        elif pings > max_pings:
            msg = f"-------- Job {job_id} did not complete within {round(end - start)} seconds and {pings} pings (max pings {max_pings})"
            logger.debug(status)
            working = False
        else:
            msg = f"-------- Job {job_id} delivered an invalid status. {round(end - start)} seconds and {pings} pings -------"
            logger.debug(status)
            working = False

    return {
        "completed": completed,
        "message": msg,
        "job_id": job_id,
        "endpoint": endpoint,
        "pings": pings,
        "elapsed": round(time.time() - start),
        "job_status": status["data"].get("job_status"),
    }
