# IIIF LTS Library

This is a Python library which facilitates interacting with the Harvard LTS (Library Technology Services) media ingest solution, which takes images and metadata and serves them via [IIIF](https://iiif.io/) at scale. `IIIFingest` helps other applications manage ingest credentials, upload images to S3 for ingest, create IIIF manifests, create asset ingest requests, generate JWT tokens for signing ingest requests, and track the status of ingest jobs.

## Getting Started

### Requirements

Requires `libmagic` to be installed on the machine running `IIIFingest` for handling file object uploads. On Mac, this can be installed with

```
brew install libmagic
```

On Ubuntu, it can be installed with

```
apt install libmagic-dev
```

### Installation

To install via [pypi.org](https://pypi.org/project/IIIFingest):

```
pip install IIIFingest
```

Or from source:

```
pip install git+https://github.com/Harvard-ATG/lts-iiif-ingest-service.git
```

### Requirements

- Python 3.7+

### Using the library

```python
import boto3
import logging
from IIIFingest.auth import Credentials
from IIIFingest.client import Client

# Enable debug logging
logging.basicConfig()
logging.getLogger('IIIFingest').setLevel(logging.DEBUG)

# Configure ingest API auth credentials
jwt_creds = Credentials(
    issuer="atissuer",
    kid="atissuerdefault",
    private_key_path="path/to/private.key"
)

# Configure ingest API client
client = Client(
    account="ataccount",
    space="atspace",
    namespace="at",
    environment="qa",
    asset_prefix="myapp",
    jwt_creds=jwt_creds,
    boto_session=boto3.Session(),
)

# Define images to ingest
images = [{
    "label": "Test Image", 
    "filepath": "tests/images/mcihtest1.tif"
}]

# Define manifest-level metadata
manifest_level_metadata = {
    "labels": ["Test Manifest"],
    "summary": "A test manifest for ingest",
    "rights": "http://creativecommons.org/licenses/by-sa/3.0/",
}

# Call client methods as needed
assets = client.upload(images)
manifest = client.create_manifest(manifest_level_metadata=manifest_level_metadata, assets=assets)
result = client.ingest(manifest=manifest, assets=assets)
status = client.jobstatus(result["job_id"])

```

### Authentication

The ingest API requires [JWT tokens](https://jwt.io/) for authentication and authorization. The credentials needed to generate tokens are provided by LTS at registration time and can then be used with this library.

The `Credentials` constructor can be configured as follows:

- `issuer`:  Identifies the app or service issuing tokens.
- `kid`: Identifies the key used for signing tokens. Ingest permissions are associated with the key.
- `private_key_path`: Path to the private key provided by LTS for the given issuer.
- `private_key_string`: The private key value as a string.
- `expiration`: The length of time in seconds for which the token should be valid (default: `3600`).

Note that the `private_key_path` and `private_key_string` options are mutually exclusive.

### Client Configuration

The `Client` constructor may be configured with the following options:

- `account`: The account identifier.
- `space`: The space within the account.
- `namespace`: The NRS namespace for manifest and asset URLs.
- `agent`: Name of the agent that created the assets.
- `environment`: Ingest API environment: `dev`, `qa`, or `prod`.
- `asset_prefix`: Optional prefix to use for image asset IDs (e.g. the application name).
- `jwt_creds`: A `Credentials` instance for generating JWT tokens.
- `boto_session`: A `boto3.session.Session` instance with permission to upload images to the S3 ingest bucket.

Notes:
- LTS will provide the `account`, `space`, `namespace`, and `agent` values.
- LTS will provide the AWS credentials needed to upload images to S3. It's up to you how S3 credentials are managed, the only requirement is that a boto [session](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/session.html) is provided to the library.
- To make requests to non-prod environments (`dev` or `qa`), the client must be on VPN or the IP must be whitelisted. If the requests are coming from a cloud account, make sure to whitelist the IP range.

### Documentation & References

See the following LTS documentation for more details:

- [Authentication & Authorization](https://docs.google.com/document/d/1qKHD--VUCWH4aEXUv7E3jEf0AnLDgNyhMpSLqCqnLbY/edit#heading=h.uuca9t2f0d35)
- [Ingest API](https://docs.google.com/document/d/1seTnNx8Unwl4w4n39rdUKESuxU1IWMlpLjpZMVbsA1U/edit#heading=h.ru4gjiray64u)

## Development

### Getting setup

**Clone repo:**

```
$ git clone git@github.com:Harvard-ATG/lts-iiif-ingest-service.git
$ cd lts-iiif-ingest-service
```

**Setup python environment:**

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements-dev.txt
```

Note that this will install all packages needed for the library as well as linting and pre-commit hooks.

**Install pre-commit hooks:**

This installs [pre-commit git hooks](https://pre-commit.com/) to automatically lint and format code before committing. See the `.pre-commit-config.yaml` for specifics.

```
$ pre-commit install
```

### Testing

To run unit tests:

```
$ pytest tests/unit
```

To run functional tests (tests which hit the dev bucket via AWS cli):

```
$ pytest tests/functional
```
Note:
- To run functional test you will need to provide a `TEST_AWS_PROFILE` in your `.env` file
- You can specify a specific function via `pytest tests/unit/test_bucket.py::<functionname>`

### PyPi release
```
// VERSION = 1.0.4.1, 1.0.5, etc
$ pip install twine
$ python3 -m build # uses PyPA `build` tool: https://packaging.python.org/en/latest/tutorials/packaging-projects/
$ tar tzf dist/IIIFingest-{VERSION}.tar.gz
$ twine check dist/*
$ twine upload dist/IIIFingest-{VERSION}*
```

If you are using an API key with PyPi, your username is `__token__`. You can create a `$HOME/.pypirc` file to avoid needing to copy & paste that token ([see docs](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#create-an-account)).

### Managing auth credentials

There are two types of auth credentials that need to be managed:
1. Ingest API credentials.
2. AWS S3 credentials.

Note that the suggestions here pertain to local development only. For production environments, it's recommended to use environment variables injected via SSM or other secret management techniques.

**Ingest API credentials**:

For local development, you may find it convenient to store credentials and configuration in a folder named `auth` either in this repository or separately (`auth` is git ignored by default). The directory structure should look something like this:

```
auth
├── dev
│   ├── issuers
│   │   ├── atapp1.json
│   │   ├── atapp2.json
│   │   └── atapp3.json
│   └── keys
│       ├── atapp1
│       │   └── atapp1default
│       │       ├── private.key
│       │       └── public.key
│       ├── atapp2
│       │   └── atapp2default
│       │       ├── private.key
│       │       └── public.key
│       └── atapp3
│           └── atapp3efault
│               ├── private.key
│               └── public.key
├── qa
└── prod
```

With this approach, you can set the path in the `Credentials` constructor:

```
private_key_path = "auth/{env}/keys/{issuer}/{issuer}default/private.key"
```

**AWS S3 credentials**:

For local development, you may choose to create a profile in `~/.aws/credentials` and reference that profile when creating the `boto3.Session` or set [environment variables](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables) that boto3 can automatically load. 

## License

Apache 2.0, see [LICENSE](LICENSE.md) for details.
