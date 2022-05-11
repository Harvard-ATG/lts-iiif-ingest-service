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
MPS_INGEST_ENDPOINT = (
    "https://mps-ingest-{environment}.lib.harvard.edu/admin/ingest/initialize"
)
MPS_JOBSTATUS_ENDPOINT = (
    "https://mps-ingest-{environment}.lib.harvard.edu/admin/ingest/jobstatus/"
)

# Base URL for images
MPS_ASSET_BASE_URL = (
    "https://mps-{environment}.lib.harvard.edu/assets/images/{namespace}:"
)

# Base URL for manifests
# The format should be URN-3:{namespace}:{manifest_name}:MANIFEST:{PreziVersion}
MPS_MANIFEST_BASE_URL = "https://nrs-{environment}.lib.harvard.edu/URN-3:{namespace}:"
