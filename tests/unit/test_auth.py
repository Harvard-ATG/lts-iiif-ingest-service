from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import jwt

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


def test_make_jwt(mocker):
    issuer = "atdarth"
    resources = ["ingest"]
    kid = "atdarthdefault"
    private_key = "secret"
    algorithm = "HS256"
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
