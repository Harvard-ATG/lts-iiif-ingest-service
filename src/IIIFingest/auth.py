import logging
import os
from datetime import datetime, timedelta

import jwt

# Backports supports Python 3.6-3.8
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from .settings import ROOT_DIR

logger = logging.getLogger(__name__)


class Credentials:
    def __init__(
        self,
        issuer: str = None,
        kid: str = None,
        resources: list = ["ingest"],
        algorithm: str = "RS256",
        expiration: int = 3600,
        timezone: str = "America/New_York",
        private_key_path: str = None,
        private_key_string: str = None,
    ):
        """
        issuer: the service which issued the token. Example: 'atdarth'
        private_key_path: path to the secret key provided by LTS for the given issuer
        private_key: stringified secret key
        ** either private_key_path or private_key is required. If both are provided, a conflict will be logged and the stringified version will be used**

        kid: key ID. Example: 'atdarthdefault'. A warning is logged if this is not passed, and the pattern f"{issuer}default" used
        resources: a list of resource types that the token is allowed to access
        expiration: length of time in seconds for which the token should be valid
        timezone: defaults to East Coast time
        algorithm: defaults to RS256
        """
        if not issuer:
            env_issuer = os.environ.get("LTS_IIIF_ISSUER")
            if env_issuer:
                logger.info("No issuer passed, using environment variable")
                self.issuer = env_issuer
            else:
                raise ValueError(
                    "No parameter passed or environment variable set for `LTS_IIIF_ISSUER`"
                )
        else:
            self.issuer = issuer

        if kid:
            self.kid = kid
        elif os.environ.get("LTS_IIIF_KID"):
            logger.info("No `kid` passed, using environment variable")
            self.kid = os.environ.get("LTS_IIIF_KID")
        else:
            self.kid = f"{self.issuer}default"
            logger.warning(f"No kid set, using {self.issuer}default")

        private_key_path_env = os.environ.get("LTS_IIIF_PRIVATE_KEY_PATH")
        private_key_string_env = os.environ.get("LTS_IIIF_PRIVATE_KEY_STRING")
        if (private_key_path_env or private_key_string_env) and (
            private_key_path or private_key_string
        ):
            logger.warning(
                "Environment variables present and args set; defaulting to args"
            )
        if private_key_path and private_key_string:
            logger.warning(
                "Both `private_key_path` and `private_key_string` set as params. Defaulting to `private_key_string`"
            )
            self.private_key = private_key_string
        elif private_key_string:
            self.private_key = private_key_string
        elif private_key_path:
            self.private_key = open(private_key_path, "r").read()
        elif private_key_string_env:
            self.private_key = private_key_string_env
        elif private_key_path_env:
            self.private_key = open(private_key_path_env, "r").read()
        else:
            raise ValueError(
                "No args (`private_key_path` or `private_key_string`) provided. Neither `LTS_IIIF_PRIVATE_KEY_PATH` nor `LTS_IIIF_PRIVATE_KEY_STRING` are set."
            )

        valid_resources = ["ingest", "content", "description"]
        for r in resources:
            if r not in valid_resources:
                raise ValueError("Invalid resource type provided")
        self.resources = resources

        self.algorithm = algorithm
        self.expiration = expiration
        self.timezone = timezone

    def make_jwt(
        self,
        resources: list = None,
        algorithm: str = None,
        expiration: int = None,
        timezone: str = None,
    ):
        """
        Makes a JWT token
        Example token data
        Header
            {
                "alg": "RS256",
                "typ": "JWT",
                "iss": "testissuer",
                "kid": "testkeyid",
                "resources": [
                    "description"
                ]
            }

        Payload
        {
            "iat": 1619628554,
            "exp": 3239257168
        }

        Valid algs: RS256, ???
        Exp range: <8 hours maximum

        """
        logger.info("Making IIIF LTS jwt")
        if not resources:
            resources = self.resources
        if not algorithm:
            algorithm = self.algorithm
        if not expiration:
            expiration = self.expiration
        if not timezone:
            timezone = self.timezone

        timestamp = datetime.now(ZoneInfo(timezone))
        header = {
            "typ": "JWT",
            "alg": algorithm,
            "iss": self.issuer,
            "kid": self.kid,
            "resources": resources,
        }
        payload = {"iat": timestamp, "exp": timestamp + timedelta(seconds=expiration)}

        encoded_jwt = jwt.encode(
            payload, self.private_key, algorithm=algorithm, headers=header
        )
        return encoded_jwt


def test():
    creds = Credentials(
        issuer="atdarth",
        resources=["ingest"],
        kid="atdarthdefault",
        private_key_path=os.path.join(
            ROOT_DIR, "auth/qa/keys/atdarth/atdarthdefault/private.key"
        ),
    )
    print(creds)
    jwt = creds.make_jwt()
    print(jwt)


if __name__ == '__main__':
    test()
