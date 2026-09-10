import time
from logger import log

RATING_UPDATE_RETRY_DELAYS = [
    3,
    5,
    15
]

class RatingUpdater:

    def __init__(
        self,
        api,
        player_id
    ):
        self.api = api
        self.player_id = player_id
        self.previous_data = None
        self.session_start_data = None

    def fetch_rating_data(self):

        return self.api.get_player_rating(
            self.player_id
        )

    def process_rating_update(
        self,
        current_data,
    ):

        # The first successful rating fetch defines the starting
        # point for this session.
        if self.session_start_data is None:

            self.session_start_data = current_data.copy()

        rating_changes = self.calculate_changes(
            current_data
        )

        session_changes = self.calculate_session_changes(
            current_data
        )

        changes = {
            **rating_changes,
            **session_changes,
        }

        self.previous_data = current_data

        return current_data, changes


    def calculate_changes(self, current_data):
        """
        Calculate rating and rank changes compared with the
        previous update.

        Missing values, such as an unranked player with rank=None,
        are handled safely.
        """

        changes = {
            "overall_rating_change": 0,
            "overall_rank_change": None,

            "season_rating_change": 0,
            "season_rank_change": None,
        }

        if self.previous_data is None:
            return changes

        # Overall rating

        previous_overall_rating = (
            self.previous_data["overall"].get("rating")
        )

        current_overall_rating = (
            current_data["overall"].get("rating")
        )

        if (
            previous_overall_rating is not None
            and current_overall_rating is not None
        ):
            changes["overall_rating_change"] = (
                current_overall_rating
                - previous_overall_rating
            )

        # Overall rank

        previous_overall_rank = (
            self.previous_data["overall"].get("rank")
        )

        current_overall_rank = (
            current_data["overall"].get("rank")
        )

        if (
            previous_overall_rank is not None
            and current_overall_rank is not None
        ):
            changes["overall_rank_change"] = (
                previous_overall_rank
                - current_overall_rank
            )

        # Season rating

        previous_season_rating = (
            self.previous_data["season"].get("rating")
        )

        current_season_rating = (
            current_data["season"].get("rating")
        )

        if (
            previous_season_rating is not None
            and current_season_rating is not None
        ):
            changes["season_rating_change"] = (
                current_season_rating
                - previous_season_rating
            )

        # Season rank

        previous_season_rank = (
            self.previous_data["season"].get("rank")
        )

        current_season_rank = (
            current_data["season"].get("rank")
        )

        if (
            previous_season_rank is not None
            and current_season_rank is not None
        ):
            changes["season_rank_change"] = (
                previous_season_rank
                - current_season_rank
            )

        return changes

    def calculate_session_changes(self, current_data):
        """
        Calculate rating and rank changes compared with the
        starting values of the current tool session.

        The session baseline is created during the first successful
        rating update after the tool starts.
        """

        changes = {
            "overall_session_rating_change": 0,
            "overall_session_rank_change": None,

            "season_session_rating_change": 0,
            "season_session_rank_change": None,
        }

        if self.session_start_data is None:
            return changes

        # --------------------------------------------------
        # OVERALL RATING
        # --------------------------------------------------

        starting_overall_rating = (
            self.session_start_data["overall"].get("rating")
        )

        current_overall_rating = (
            current_data["overall"].get("rating")
        )

        if (
            starting_overall_rating is not None
            and current_overall_rating is not None
        ):
            changes["overall_session_rating_change"] = (
                current_overall_rating
                - starting_overall_rating
            )

        # --------------------------------------------------
        # OVERALL RANK
        # --------------------------------------------------

        starting_overall_rank = (
            self.session_start_data["overall"].get("rank")
        )

        current_overall_rank = (
            current_data["overall"].get("rank")
        )

        if (
            starting_overall_rank is not None
            and current_overall_rank is not None
        ):
            changes["overall_session_rank_change"] = (
                starting_overall_rank
                - current_overall_rank
            )

        # --------------------------------------------------
        # SEASON RATING
        # --------------------------------------------------

        starting_season_rating = (
            self.session_start_data["season"].get("rating")
        )

        current_season_rating = (
            current_data["season"].get("rating")
        )

        if (
            starting_season_rating is not None
            and current_season_rating is not None
        ):
            changes["season_session_rating_change"] = (
                current_season_rating
                - starting_season_rating
            )

        # --------------------------------------------------
        # SEASON RANK
        # --------------------------------------------------

        starting_season_rank = (
            self.session_start_data["season"].get("rank")
        )

        current_season_rank = (
            current_data["season"].get("rank")
        )

        if (
            starting_season_rank is not None
            and current_season_rank is not None
        ):
            changes["season_session_rank_change"] = (
                starting_season_rank
                - current_season_rank
            )

        return changes

    def handle_game_end(
        self,
        stop_event,
        on_rating_updated,
        rating_update_delay
    ):
        """
        Handle the rating update process after a game has ended.

        Wait for the configured delay, retrieve the updated rating
        data, notify the caller, and log the result.
        """

        if rating_update_delay > 0:

            log(
                f"Waiting {rating_update_delay} seconds "
                "before updating rating..."
            )

        # Wait, but allow the watcher to be stopped immediately.

        if stop_event.wait(rating_update_delay):

            return False

        try:

            data, changes = self.update_rating_with_retry(
                retry_delays=RATING_UPDATE_RETRY_DELAYS,
                stop_event=stop_event
            )

            if data is not None:

                on_rating_updated(
                    data,
                    changes,
                    update_match_changes=True,
                    trigger_match_overlays=True
                )

                overall_rating_change = (
                    self.format_change(
                        changes["overall_rating_change"]
                    )
                )

                season_rating_change = (
                    self.format_change(
                        changes["season_rating_change"]
                    )
                )

                log("Rating updated successfully.")

                log(
                    f"Overall Rating: "
                    f"{data['overall']['rating']} "
                    f"({overall_rating_change})"
                )

                log(
                    f"Seasonal Rating: "
                    f"{data['season']['rating']} "
                    f"({season_rating_change})"
                )

            else:

                log(
                    "Rating update skipped. "
                    "The latest match is not available yet."
                )

        except Exception as error:

            log()

            log(
                f"Rating update failed: {error}"
            )

        log()

        log(
            "Waiting for the next game..."
        )

        return True

    def format_change(self,value):

        if value is None:
            return "N/A"

        if value >= 0:
            return f"+{value}"

        return str(value)

    def update_rating_with_retry(
        self,
        retry_delays=None,
        stop_event=None
    ):
        """
        Fetch the latest rating data and retry if the latest
        game has not yet been processed by Strata.

        Only writes output files once the final accepted result
        has been determined.
        """

        if retry_delays is None:

            retry_delays = RATING_UPDATE_RETRY_DELAYS

        baseline_data = self.previous_data

        delays = list(retry_delays)

        attempt = 1

        while True:

            try:

                log(
                    f"Checking Strata for updated rating "
                    f"(attempt {attempt})..."
                )

                current_data = (
                    self.fetch_rating_data()
                )

            except Exception as error:

                current_data = None

                log(
                    f"Rating update attempt {attempt} failed: "
                    f"{error}"
                )

            if current_data is not None:

                if baseline_data is None:

                    return self.process_rating_update(
                        current_data,
                    )

                if self.has_match_data_changed(
                    baseline_data,
                    current_data
                ):

                    return self.process_rating_update(
                        current_data,
                    )

                if not delays:

                    log(
                        "Latest match was not detected after "
                        "all retry attempts."
                    )

                    return None, None

            delay = delays.pop(0)

            attempt += 1

            log(
                "Latest match not yet available on Strata."
            )

            log(
                f"Retrying in {delay} seconds..."
            )

            if stop_event is not None:

                if stop_event.wait(delay):

                    raise RuntimeError(
                        "Rating update was cancelled."
                    )

            else:

                time.sleep(delay)

    def has_match_data_changed(
        self,
        previous_data,
        current_data
    ):
        """
        Check whether Strata has processed a new match.

        Match counts are used as the primary indicator that
        the latest game result is available.
        """

        previous_overall_matches = (
            previous_data["overall"].get("matches")
        )

        current_overall_matches = (
            current_data["overall"].get("matches")
        )

        if (
            previous_overall_matches is not None
            and current_overall_matches is not None
            and current_overall_matches
            != previous_overall_matches
        ):
            return True

        previous_season_matches = (
            previous_data["season"].get("matches")
        )

        current_season_matches = (
            current_data["season"].get("matches")
        )

        if (
            previous_season_matches is not None
            and current_season_matches is not None
            and current_season_matches
            != previous_season_matches
        ):
            return True

        return False