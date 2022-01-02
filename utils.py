import io
import logging
import os
from typing import Dict, Any, Optional

import boto3  # type: ignore
import botocore  # type: ignore


class DigitalOcean:
    _session: boto3.session.Session

    _spaces_conf: Dict[str, Any] = {
        "service_name": "s3",
        "region_name": "nyc3",
        "endpoint_url": "https://nyc3.digitaloceanspaces.com",
    }

    def __init__(self, spaces_conf: Optional[Dict[str, Any]] = None) -> None:
        self.log: logging.Logger = logging.getLogger(f"{self.__class__.__name__}")

        if spaces_conf is not None:
            self._spaces_conf.update(spaces_conf)

        for k, e in [
            ("aws_access_key_id", "DIGITALOCEAN_SPACES_KEY_ID"),
            ("aws_secret_access_key", "DIGITALOCEAN_SPACES_SECRET"),
        ]:
            if self._spaces_conf.get(k) is None:
                self._spaces_conf[k] = os.getenv(e)

        self._session = boto3.session.Session()
        self._spaces_client = self._session.client(**self._spaces_conf)

    def get_object(self, space: str, key: str) -> io.BytesIO:
        """
        Fetches an object from a space by it's key.

        :param space: The object space
        :param key: The object key
        :return: A io.BytesIO buffer with the contents of the file
        """
        buffer: io.BytesIO = io.BytesIO()
        self._spaces_client.download_fileobj(Bucket=space, Key=key, Fileobj=buffer)
        buffer.seek(0)
        return buffer