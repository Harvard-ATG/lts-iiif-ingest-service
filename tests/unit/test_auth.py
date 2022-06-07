import os
import tempfile
from datetime import datetime, timedelta
from unittest import mock
from zoneinfo import ZoneInfo

import jwt
import pytest

from IIIFingest.auth import Credentials


def test_create_credentials_with_defaults():
    issuer = "atdarth"
    resources = ["ingest"]
    kid = "atdarthdefault"
    private_key = "secret"

    creds = Credentials(
        issuer=issuer, resources=resources, kid=kid, private_key_string=private_key
    )

    assert creds.issuer == issuer
    assert creds.kid == kid
    assert creds.private_key == private_key
    assert creds.resources == resources
    assert creds.algorithm == "RS256"
    assert creds.expiration == 3600
    assert creds.timezone == "America/New_York"


def test_create_credentials_raises_error_without_private_key():
    with pytest.raises(ValueError):
        Credentials(issuer="atdarth", kid="atdarthdefault")


@mock.patch.dict(os.environ, {"LTS_IIIF_ISSUER": "atdarth"}, clear=True)
def test_create_credentials_with_env_issuer():
    creds = Credentials(kid="atdarthdefault", private_key_string="secret")
    assert creds.issuer == "atdarth"


@mock.patch.dict(os.environ, {"LTS_IIIF_KID": "atdarthdefault"}, clear=True)
def test_create_credentials_with_env_kid():
    creds = Credentials(issuer="atdarth", private_key_string="secret")
    assert creds.kid == "atdarthdefault"


@mock.patch.dict(
    os.environ, {"LTS_IIIF_PRIVATE_KEY_STRING": "secret123string"}, clear=True
)
def test_create_credentials_with_env_private_key_string():
    creds = Credentials(issuer="atdarth", kid="atdarthdefault")
    assert creds.private_key == "secret123string"


def test_create_credentials_with_env_private_key_path():
    private_key = "secret123file"

    with tempfile.NamedTemporaryFile() as fp:
        fp.write(private_key.encode('utf-8'))
        fp.flush()
        private_key_path = fp.name

        with mock.patch.dict(
            os.environ, {"LTS_IIIF_PRIVATE_KEY_PATH": private_key_path}
        ):
            creds = Credentials(issuer="atdarth", kid="atdarthdefault")
            assert creds.private_key == private_key


@mock.patch.dict(
    os.environ,
    {
        "LTS_IIIF_PRIVATE_KEY_STRING": "secret123string",
        "LTS_IIIF_PRIVATE_KEY_PATH": "/tmp/fake_private.key",
    },
    clear=True,
)
def test_create_credentials_with_env_private_key_string_and_path():
    creds = Credentials(issuer="atdarth", kid="atdarthdefault")
    assert creds.private_key == "secret123string"


def test_make_jwt(mocker):
    # NOTE: Using HS256 JWT algorithm to avoid generating a pub/priv key
    issuer = "atdarth"
    resources = ["ingest"]
    kid = "atdarthdefault"
    private_key = "secret"
    algorithm = "HS256"  # TODO: shouldn't this be RS256?
    expiration = 3600
    timezone = "America/New_York"

    timestamp = datetime(2022, 6, 7, 5, 41, 43, 275100, tzinfo=ZoneInfo(timezone))
    mock_datetime = mocker.patch('IIIFingest.auth.datetime', return_value=timestamp)
    mock_datetime.now.return_value = timestamp

    header = {
        "typ": "JWT",
        "alg": algorithm,
        "iss": issuer,
        "kid": kid,
        "resources": resources,
    }
    payload = {"iat": timestamp, "exp": timestamp + timedelta(seconds=expiration)}
    expected_jwt = jwt.encode(payload, private_key, algorithm=algorithm, headers=header)

    creds = Credentials(
        issuer=issuer,
        resources=resources,
        algorithm=algorithm,
        expiration=expiration,
        timezone=timezone,
        kid=kid,
        private_key_string=private_key,
    )

    actual_jwt = creds.make_jwt()

    assert actual_jwt == expected_jwt
