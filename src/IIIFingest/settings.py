import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# MPS environments
VALID_ENVIRONMENTS = ("dev", "qa", "prod")

# MPS Bucket used by ingest process
MPS_BUCKET_NAME = "edu.harvard.huit.lts.mps.{account}-{space}-{environment}"

# MPS API endpoints - dev (older network restricted ALBs)
MPS_INGEST_ENDPOINT_PRIVATE = (
    "https://mps-admin-{environment}.lib.harvard.edu/admin/ingest/initialize"
)
MPS_JOBSTATUS_ENDPOINT_PRIVATE = (
    "https://mps-admin-{environment}.lib.harvard.edu/admin/ingest/jobstatus/"
)

# MPS API endpoints - QA and prod (new public ALBs)
MPS_INGEST_ENDPOINT_QA = "https://mps-ingest-qa.lib.harvard.edu/admin/ingest/initialize"
MPS_JOBSTATUS_ENDPOINT_QA = (
    "https://mps-ingest-qa.lib.harvard.edu/admin/ingest/jobstatus/"
)
MPS_INGEST_ENDPOINT_PROD = "https://mps-ingest.lib.harvard.edu/admin/ingest/initialize"
MPS_JOBSTATUS_ENDPOINT_PROD = (
    "https://mps-ingest.lib.harvard.edu/admin/ingest/jobstatus/"
)

# Base URL for images
MPS_ASSET_BASE_URL = (
    "https://mps-{environment}.lib.harvard.edu/assets/images/{namespace}:"
)
MPS_ASSET_BASE_URL_PROD = "https://mps.lib.harvard.edu/assets/images/{namespace}:"

# Base URL for manifests
# The format should be URN-3:{namespace}:{manifest_name}:MANIFEST:{PreziVersion}
MPS_MANIFEST_BASE_URL = "https://nrs-{environment}.lib.harvard.edu/URN-3:{namespace}:"
MPS_MANIFEST_BASE_URL_PROD = "https://nrs.lib.harvard.edu/URN-3:{namespace}:"

# Service status endpoints
MPS_DEV_INGEST_SERVICE_STATUS = (
    "https://mps-admin-dev.lib.harvard.edu/admin/ingest/version"
)
MPS_QA_INGEST_SERVICE_STATUS = (
    "https://mps-ingest-qa.lib.harvard.edu/admin/ingest/version"
)
MPS_PROD_INGEST_SERVICE_STATUS = (
    "https://mps-ingest.lib.harvard.edu/admin/ingest/version"
)
