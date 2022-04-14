import logging
import time
from datetime import datetime
from typing import Optional

# from urllib import request
from zoneinfo import ZoneInfo

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

logger = logging.getLogger(__name__)


def signed_request(
    method: str,
    url: str,
    creds,  # AWS credentials
    region: str = "us-east-1",
    service_name: str = "lambda",
    data: Optional[dict] = None,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
):
    """Sign requests which will be proxied to the ingest endpoint through AWS Lambda function URLs"""
    request = AWSRequest(
        method=method, url=url, data=data, params=params, headers=headers
    )
    # "service_name" is generally "execute-api" for signing API Gateway requests
    SigV4Auth(creds, service_name, region).add_auth(request)
    return requests.request(
        method=method, url=url, headers=dict(request.headers), data=data
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


def sendIngestRequest(
    req: dict,
    endpoint: str,
    token: str,
    proxies: Optional[dict] = None,
    session=Optional[boto3.Session],
) -> requests.Response:

    if proxies is not None:
        try:
            proxy = proxies.get("https")
            data = {"endpoint": endpoint, "req": req}
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/x-amz-json-1.1",
            }
            # Requests to the proxy need to be signed - Lambda function URL, using AWS IAM auth
            # If we can't get lambda:InvokeFunctionUrl permissions on the MPS S3 roles, we will need to manage a second set of IAM users AT controls and use that boto session here
            # May need to move the token from headers to the body depending on how the IAM signing works, which would create divergence between the request formats
            if not session:
                session = boto3._get_default_session()
            credentials = session.get_credentials()
            creds = credentials.get_frozen_credentials()
            # r = requests.post(
            #     proxy,
            #     headers={"Authorization": f"Bearer {token}"},
            #     json={"endpoint": endpoint, "req": req},
            # )
            r = signed_request(
                method="POST", url=proxy, creds=creds, data=data, headers=headers
            )
        except Exception as e:
            # Key Error - should also have an exception for the session not working
            logger.error("HTTPS proxy not found in proxy dict.")
            logger.error(e)

    else:
        r = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {token}"},
            json=req,
        )
    return r


def jobStatus(
    job_id: str,
    endpoint: str = "https://mps-admin-qa.lib.harvard.edu/admin/ingest/jobstatus/",
    proxies: Optional[dict] = None,
) -> requests.Response:
    url = f"{endpoint}{job_id}"
    if proxies is not None:
        try:
            proxy = proxies.get("https")
            params = {"job_url": url}
            r = requests.get(proxy, params=params)
        except Exception as e:
            logger.error(
                "HTTPS proxy not found in proxy dict. Getting job status without proxy."
            )
            logger.error(e)
            r = requests.get(url)
    else:
        r = requests.get(url)
    return r


def pingJob(
    job_id: str,
    endpoint: str = "https://mps-admin-qa.lib.harvard.edu/admin/ingest/jobstatus/",
    max_pings: int = 25,
    interval: int = 10,
    proxies: Optional[dict] = None,
) -> dict:
    working = True
    completed = False
    start = time.time()
    pings = 0
    status = {}
    while working:
        pings += 1
        r = jobStatus(job_id, endpoint, proxies=proxies)
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
