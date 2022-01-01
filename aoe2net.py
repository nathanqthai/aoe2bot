import enum
import logging
from typing import Dict, Optional, Any, Union, List

import requests  # type: ignore


class AoE2net:
    """https://aoe2.net/#api"""

    class LeaderboardID(enum.IntEnum):
        UNRANKED = 0
        DEATHMATCH = 1
        TEAM_DEATHMATCH = 2
        RANDOM_MAP = 3
        TEAM_RANDOM_MAP = 4
        EMPIRE_WARS = 13
        TEAM_EMPIRE_WARS = 14

    _base_url: str = "https://aoe2.net/api"
    _base_params: Dict[str, Any] = {"game": "aoe2de"}
    _strings: Optional[Dict[str, Any]] = None

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
        method: str = "GET",
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        A helper function to make API requests.

        :param endpoint: The endpoint to call
        :param method: The HTTP method to be used
        :param params: The parameters to be used
        :raises: Raises an an error on any HTTP request failure
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

    def strings(self, language: str = "en") -> Dict[str, Any]:
        """
        Request a list of strings used by the API.

        :param language: Language (en, de, el, es, es-MX, fr, hi, it, ja, ko, ms, nl, pt, ru, tr, vi, zh, zh-TW)
        :return: A dictionary of the strings
        """
        self.log.debug("Fetching strings...")
        if (self._strings is None) or (
            language != self._strings.get("language", "none")
        ):
            self._strings = self.call_api("strings", params={"language": language})
        self.log.debug(self._strings)
        return self._strings

    def leaderboard(
        self,
        start: int = 1,
        count: int = 10000,
        board: LeaderboardID = LeaderboardID.RANDOM_MAP,
        name: Optional[str] = None,
        steam_id: Optional[Union[int, str]] = None,
        profile_id: Optional[Union[int, str]] = None,
    ) -> Dict[str, Any]:
        """
        Request the current leaderboards.

        :param start: Starting rank (Ignored if search, steam_id, or profile_id are defined)
        :param count: Number of leaderboard entries to get (Must be 10000 or less))
        :param board: Leaderboard ID (
                Unranked=0,
                1v1 Deathmatch=1, Team Deathmatch=2,
                1v1 Random Map=3, Team Random Map=4,
                1v1 Empire Wars=13, Team Empire Wars=14
            )
        :param name: Name Search
        :param steam_id: steamID64 (ex: 76561199003184910)
        :param profile_id: Profile ID (ex: 459658)
        :return:
        """
        params: Dict[str, Any] = {
            "start": start,
            "count": count,
            "leaderboard_id": board.value,
        }
        if name:
            params.update({"search": name})
        if steam_id:
            params.update({"steam_id": steam_id})
        if profile_id:
            params.update({"profile_id": profile_id})
        params.update(self._base_params)
        self.log.debug("Fetching leaderboard...")
        leaderboard = self.call_api("leaderboard", params=params)
        self.log.debug(leaderboard)
        return leaderboard

    def search(
        self, name: str, board: LeaderboardID = LeaderboardID.RANDOM_MAP
    ) -> List[Dict[str, Any]]:
        """
        Searches a leaderboard for a given player name and returns all matches.

        :param name: The player name
        :param board: Leaderboard ID (
                Unranked=0,
                1v1 Deathmatch=1, Team Deathmatch=2,
                1v1 Random Map=3, Team Random Map=4,
                1v1 Empire Wars=13, Team Empire Wars=14
            )
        :return: The list of players
        """
        self.log.debug(f"Searching for {name}")
        return self.leaderboard(board=board, name=name).get("leaderboard", [])

    def find_name(
        self, name: str, board: LeaderboardID = LeaderboardID.RANDOM_MAP
    ) -> Optional[Dict[str, Any]]:
        """
        Performs a case-insensitive player search and returns only exact matches.

        :param name: The player name, will be search as all lowercase
        :param board: Leaderboard ID (
                Unranked=0,
                1v1 Deathmatch=1, Team Deathmatch=2,
                1v1 Random Map=3, Team Random Map=4,
                1v1 Empire Wars=13, Team Empire Wars=14
            )
        :return: The player information
        """
        players: List[Dict[str, Any]] = self.search(name, board)

        matched_player: Optional[Dict[str, Any]] = None
        for player in players:
            if player.get("name", "").lower() == name.lower():
                matched_player = player
                break

        return matched_player

    def lookup_string(self, key: str, key_id: int) -> Optional[str]:
        s: Optional[str] = None
        for lookups in self._strings.get(key, []):
            if lookups["id"] == key_id:
                s = lookups["string"]
                break
        return s
