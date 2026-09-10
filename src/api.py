import requests


BASE_URL = "https://strata.gamereplays.org/api"

class NoLinkedPlayersError(RuntimeError):
    """
    Raised when the authenticated Strata account has no linked
    GO accounts.
    """

    pass

class StrataAPI:

    def __init__(self, token):

        self.token = token

        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }


    def _get_rating_data(self):
        """
        Retrieve raw rating data for all GO accounts linked to
        the authenticated Strata account.
        """

        url = (
            f"{BASE_URL}/me/leagues/1/rating"
            "?include_rank=true&include_peak=true"
        )

        try:

            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )

        except requests.RequestException as error:

            raise RuntimeError(
                f"Could not connect to the Strata API: {error}"
            ) from error

        if response.status_code == 401:

            raise RuntimeError(
                "API authentication failed. The bearer token may be invalid."
            )

        if response.status_code == 403:

            raise RuntimeError(
                "Access denied."
            )

        if response.status_code != 200:

            raise RuntimeError(
                f"Strata API returned HTTP {response.status_code}: "
                f"{response.text}"
            )

        try:

            response_data = response.json()

        except ValueError as error:

            raise RuntimeError(
                "Strata API returned invalid JSON."
            ) from error

        try:

            players = response_data["data"]

        except KeyError as error:

            raise RuntimeError(
                "Strata API response did not contain player data."
            ) from error

        if not players:

            raise NoLinkedPlayersError

        return players


    def get_available_players(self):
        """
        Retrieve the GO player IDs linked to the authenticated
        Strata account.
        """

        players = self._get_rating_data()

        return [
            int(player_id)
            for player_id in players.keys()
        ]


    def get_player_rating(self, player_id):
        """
        Retrieve rating information for a specific GO account
        linked to the authenticated Strata account.
        """

        players = self._get_rating_data()

        try:

            return players[str(player_id)]

        except KeyError as error:

            raise RuntimeError(
                f"Player ID {player_id} was not found in the API response."
            ) from error