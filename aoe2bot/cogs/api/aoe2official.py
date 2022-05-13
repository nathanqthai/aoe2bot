import enum
import logging
from typing import Dict, Optional, Any, Union, List

import requests  # type: ignore


class AoE2official:
    """https://api.ageofempires.com/api/v2/"""

    class GameMode(enum.Enum):
        EMPIRE_WARS = "Empire Wars"
        RANDOM_MAP = "Random Map"

    class MatchSize(enum.Enum):
        ONE_V_ONE = "1v1"
        TWO_V_TWO = "2v2"
        THREE_V_THREE = "3v3"
        FOUR_V_FOUR = "4v4"

    _base_url: str = "https://api.ageofempires.com/api/v2/AgeII/GetGlobalStats"

    payload = {
        "isRanked": True,
        "gameMode": "Random Map",
        "matchSize": "1v1",
        "mapSize": "Large",
    }

    def __init__(
        self,
        base_url: Optional[str] = None,
        base_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initializes the API class.

        :param base_url: The base API url, defaults to `https://aoe2.net/api`
        :param base_params: The default parameters for all requests, defaults to `game=aoe2de`
        """
        self.log: logging.Logger = logging.getLogger(f"{self.__class__.__name__}")
        if base_url is not None:
            self._base_url = base_url
        if base_params is not None:
            self._base_params = base_params
        self._strings = self.strings()

        self.log.debug(f"Initialized {self.__class__.__name__}")

    def call_api(
        self,
        endpoint: str,
        method: str = "POST",
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        A helper function to make API requests.

        :param endpoint: The endpoint to call
        :param method: The HTTP method to be used
        :param params: The parameters to be used
        :raises: Raises an error on any HTTP request failure
        :return: A dictionary of the JSON API response
        """
        url = f"{self._base_url}/{endpoint}"
        if params:
            params.update(self._base_params)
        else:
            params = self._base_params
        self.log.debug(f"Calling {url} with {params}")

        try:
            response: requests.Response = requests.request(
                method=method, url=url, params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            self.log.exception(f"Failed API call")
            raise

    def global_stats(self):
        self.call_api("GetGlobalStats", params)
