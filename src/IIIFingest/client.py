import json
import logging
import os
import re
from typing import List, Optional

import requests
import shortuuid

from .asset import Asset, create_asset_id
from .generate_manifest import createManifest
from .ingest import createImageAsset, pingJob, sendIngestRequest, wrapIngestRequest
from .settings import (
    MPS_ASSET_BASE_URL,
    MPS_ASSET_BASE_URL_PROD,
    MPS_BUCKET_NAME,
    MPS_DEV_INGEST_SERVICE_STATUS,
    MPS_INGEST_ENDPOINT_PRIVATE,
    MPS_INGEST_ENDPOINT_PROD,
    MPS_INGEST_ENDPOINT_QA,
    MPS_JOBSTATUS_ENDPOINT_PRIVATE,
    MPS_JOBSTATUS_ENDPOINT_PROD,
    MPS_JOBSTATUS_ENDPOINT_QA,
    MPS_MANIFEST_BASE_URL,
    MPS_MANIFEST_BASE_URL_PROD,
    MPS_PROD_INGEST_SERVICE_STATUS,
    MPS_QA_INGEST_SERVICE_STATUS,
    VALID_ENVIRONMENTS,
)

logger = logging.getLogger(__name__)
nrs_namespace_invalid = re.compile(r"[^a-zA-Z0-9\.]")


class Client:
    """
    Constructs the ingest API client.
    """

    def __init__(
        self,
        account: str = "at",
        space: str = "atdarth",
        namespace: str = "at",
        asset_prefix: str = "",
        agent: str = "atagent",
        environment: str = "qa",
        jwt_creds=None,
        boto_session=None,
        with_uuid: bool = True,
    ):
        if not namespace or nrs_namespace_invalid.search(namespace):
            raise ValueError("Invalid or missing namespace_prefix")
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError(
                f"Invalid environment: {environment} must be one of: {VALID_ENVIRONMENTS}"
            )

        namespace = namespace.upper()

        self.account = account
        self.space = space
        self.namespace = namespace
        self.asset_prefix = asset_prefix
        self.agent = agent
        self.environment = environment
        self.jwt_creds = jwt_creds
        self.boto_session = boto_session
        self.with_uuid = with_uuid

        self.bucket_name = MPS_BUCKET_NAME.format(
            account=account, space=space, environment=environment
        )

        # Some divergence in dev/qa/prod ingest endpoint formats; prod doesn't have prod in URL, QA/Prod admin endpoint is different format than dev
        if self.environment == "dev":
            self.asset_base_url = MPS_ASSET_BASE_URL.format(
                environment=environment, namespace=namespace
            )
            self.ingest_endpoint = MPS_INGEST_ENDPOINT_PRIVATE.format(
                environment=environment
            )
            self.job_endpoint = MPS_JOBSTATUS_ENDPOINT_PRIVATE.format(
                environment=environment
            )
            self.manifest_base_url = MPS_MANIFEST_BASE_URL.format(
                environment=environment, namespace=namespace
            )
            self.ingest_service_status_endpoint = MPS_DEV_INGEST_SERVICE_STATUS
        elif self.environment == "qa":
            self.asset_base_url = MPS_ASSET_BASE_URL.format(
                environment=environment, namespace=namespace
            )
            self.ingest_endpoint = MPS_INGEST_ENDPOINT_QA
            self.job_endpoint = MPS_JOBSTATUS_ENDPOINT_QA
            self.manifest_base_url = MPS_MANIFEST_BASE_URL.format(
                environment=environment, namespace=namespace
            )
            self.ingest_service_status_endpoint = MPS_QA_INGEST_SERVICE_STATUS
        elif self.environment == "prod":
            self.asset_base_url = MPS_ASSET_BASE_URL_PROD.format(namespace=namespace)
            self.ingest_endpoint = MPS_INGEST_ENDPOINT_PROD
            self.job_endpoint = MPS_JOBSTATUS_ENDPOINT_PROD
            self.manifest_base_url = MPS_MANIFEST_BASE_URL_PROD.format(
                namespace=namespace
            )
            self.ingest_service_status_endpoint = MPS_PROD_INGEST_SERVICE_STATUS

    def _get_asset_url(self, asset_id: str) -> str:
        """Constructs the asset URL."""
        return f"{self.asset_base_url}{asset_id}"

    def _get_manifest_url(self, manifest_name: str, prezi_version: int = 3) -> str:
        """Constructs the manifest URL."""
        return f"{self.manifest_base_url}{manifest_name}:MANIFEST:{prezi_version}"

    def upload(
        self, images: List[dict], s3_path: str = "", with_uuid=None
    ) -> List[Asset]:
        """
        Uploads a list of images to the MPS ingest bucket in S3.
        Returns a list of assets.
        image dict format
        {
            "id": "id123",
            "label": "",
            "filepath": ".../lts-iiif-ingest-service/tests/images/27.586.1-cm-2016-02-09.tif", # either filepath or fileobj is required
            "fileobj": "", # either filepath or fileobj is required,
            "asset_id": "mcih235dad6fd15742bc91d167cbd59c7756" # no dashes allowed
        }
        """
        if with_uuid is None:
            with_uuid = self.with_uuid
        logger.debug(f"Uploading {len(images)} images")
        assets = []
        for image in images:
            if image.get("asset_id"):
                asset_id = image.get("asset_id")
            else:
                asset_id = create_asset_id(
                    asset_prefix=self.asset_prefix,
                    identifier=image.get("id"),
                    with_uuid=with_uuid,
                )

            if "filepath" in image:
                filepath = image["filepath"]
                asset = Asset.from_file(
                    filepath, asset_id=asset_id, label=image.get("label")
                )
            elif "fileobj" in image:
                fileobj = image["fileobj"]
                asset = Asset.from_fileobj(
                    fileobj, asset_id=asset_id, label=image.get("label")
                )
            asset.upload(
                bucket_name=self.bucket_name,
                s3_path=s3_path,
                boto_session=self.boto_session,
            )
            assets.append(asset)
        logger.debug(f"Upload completed. Returning assets: {assets}")
        return assets

    def create_manifest(
        self,
        manifest_level_metadata: dict,
        assets: List[Asset],
        manifest_name: str = "",
        prezi_version: int = 3,
    ) -> dict:
        """
        Creates a manifest from manifest level metadata and a list of image assets.
        Returns the created manifest as a dict.
        """
        if not manifest_name:
            manifest_name = f"GEN{shortuuid.uuid()}"

        canvases = []
        for asset in assets:
            canvas = asset.to_dict()
            canvas["id"] = self._get_asset_url(asset.asset_id)
            canvas["service"] = f"/full/max/0/default{asset.extension}"
            canvases.append(canvas)

        logger.debug(f"Creating manifest from data: {manifest_level_metadata}")
        manifest_kwargs = dict(
            base_url=self._get_manifest_url(
                manifest_name=manifest_name, prezi_version=prezi_version
            ),
            canvases=canvases,
            labels=manifest_level_metadata.get("labels", None),
            behaviors=manifest_level_metadata.get("behaviors", None),
            providers=manifest_level_metadata.get("providers", None),
            rights=manifest_level_metadata.get("rights", None),
            required_statement=manifest_level_metadata.get("required_statement", None),
            manifest_metadata=manifest_level_metadata.get("metadata", None),
            default_lang=manifest_level_metadata.get(
                "default_lang", None
            ),  # need to add this?
            service_type=manifest_level_metadata.get(
                "service_type", None
            ),  # need to add this ?
            service_profile=manifest_level_metadata.get(
                "service_profile", None
            ),  # need to add this
        )
        manifest = createManifest(
            **{k: v for k, v in manifest_kwargs.items() if v is not None}
        )
        manifest_json = manifest.json_dumps()
        logger.debug(f"Created manifest: {manifest_json}")

        manifest_dict = json.loads(manifest_json)
        return manifest_dict

    def ingest(
        self,
        assets: List[Asset],
        manifest: Optional[dict] = None,
        policy_definition: Optional[dict] = None,
    ) -> dict:
        """
        Sends ingest request for assets and manifest.
        Returns the job ID.
        """
        if manifest is None:
            manifest = {}

        logger.debug(f"Preparing {len(assets)} ingest assets")
        ingest_assets = []
        for asset in assets:
            src_path, src_key = os.path.split(asset.s3key)
            params = {
                "space": self.space,
                "createdByAgent": self.agent,
                "identifier": f"{self.namespace}:{asset.asset_id}",
                "storageSrcPath": f"{src_path}/",
                "storageSrcKey": src_key,
                "policyDefinition": policy_definition,
                "assetMetadata": [
                    {
                        "fieldName": "imageSize",
                        "jsonValue": {
                            "width": asset.width,
                            "height": asset.height,
                        },
                    }
                ],
            }
            ingest_asset = createImageAsset(
                **{k: v for k, v in params.items() if v is not None}
            )
            ingest_assets.append(ingest_asset)

        token = self.jwt_creds.make_jwt()
        logger.debug(f"Generated ingest auth token: {token}")

        request_body = wrapIngestRequest(
            assets=ingest_assets,
            manifest=manifest,
            metadata={},
            space_default=self.space,
            action_default="upsert",
        )

        logger.debug(f"Sending ingest request: {request_body}")
        response = sendIngestRequest(
            req=request_body,
            endpoint=self.ingest_endpoint,
            token=token,
        )
        logger.debug(
            f"Received ingest response: {response.status_code} {response.text}"
        )
        response_data = response.json()

        job_id = (
            response_data.get("data", {}).get("job_tracker_file", {}).get("_id", "")
        )
        if not job_id:
            logger.warning("Ingest job ID not found. Maybe the ingest request failed?")
        else:
            logger.info(f"Ingest job ID: {job_id}")

        result = {
            "job_id": str(job_id),
            "error": response_data.get("error", None),
            "data": response_data.get("data", {}),
        }
        return result

    def jobstatus(self, job_id: str) -> dict:
        """
        Returns the status of an ingest request.
        """
        logger.info(f"Pinging job {job_id}")
        status = pingJob(
            job_id=job_id,
            endpoint=self.job_endpoint,
        )
        logger.info(f"Job status: {status}")

        if status.get("completed"):
            logger.debug("Job completed.")
        else:
            logger.debug("Job failed or did not complete in the allotted timeframe")

        return status

    def servicestatus(self) -> bool:
        """
        Returns whether the MPS ingest service is up or down
        """
        logger.info(f"Pinging service {self.ingest_service_status_endpoint}")
        r = requests.get(self.ingest_service_status_endpoint)
        return r.status_code == 200

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'{self.account!r}, {self.space!r}, {self.namespace!r}, {self.agent!r}, {self.asset_prefix!r})'
        )
