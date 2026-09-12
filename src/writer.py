import json
from datetime import datetime
from pathlib import Path

class OutputWriter:
    def __init__(self, output_directory):
        self.output_directory = Path(
            output_directory
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

    def write_output_files(
        self,
        data,
        player_id,
        changes,
        update_match_changes=False,
        trigger_match_overlays=False
    ):
        """
        Write all rating information to the output directory.

        Multiple output formats are generated so streamers can choose
        the exact text format they want to use in OBS.
        """

        overall = data["overall"]
        season = data["season"]

        overall_rating = overall.get("rating")
        overall_rank = overall.get("rank")

        season_rating = season.get("rating")
        season_rank = season.get("rank")

        overall_rank_change = self.format_change(
            changes["overall_rank_change"]
        )

        season_rank_change = self.format_change(
            changes["season_rank_change"]
        )

        overall_session_change = self.format_change(
            changes["overall_session_rating_change"]
        )

        overall_session_rank_change = self.format_change(
            changes["overall_session_rank_change"]
        )

        season_session_change = self.format_change(
            changes["season_session_rating_change"]
        )

        season_session_rank_change = self.format_change(
            changes["season_session_rank_change"]
        )

        overall_change = self.format_change(
            changes["overall_rating_change"]
        )

        season_change = self.format_change(
            changes["season_rating_change"]
        )

        overall_rank_number = self.format_rank_number(
            overall_rank
        )

        overall_rank_hash = self.format_rank_hash(
            overall_rank
        )

        season_rank_number = self.format_rank_number(
            season_rank
        )

        season_rank_hash = self.format_rank_hash(
            season_rank
        )

        output_files = {

            # --------------------------------------------------
            # OVERALL RATING
            # --------------------------------------------------

            "overall_rank_label.txt":
                f"Rank: {overall_rank_number}",

            "overall_elo_and_rank_label.txt":
                (
                    f"Elo: {overall_rating} "
                    f"(Rank: {overall_rank_number})"
                ),

            "overall_rank_hash.txt":
                overall_rank_hash,

            "overall_rank.txt":
                overall_rank_number,

            "overall_elo.txt":
                overall_rating,

            "overall_elo_label.txt":
                f"Elo: {overall_rating}",

            # --------------------------------------------------
            # OVERALL SESSION
            # --------------------------------------------------

            "overall_session_elo_change_label.txt":
                f"Elo: {overall_session_change}",

            "overall_session_rank_change_label.txt":
                f"Rank: {overall_session_rank_change}",

            "overall_elo_and_session_elo_change_label.txt":
                (
                    f"Elo: {overall_rating} "
                    f"({overall_session_change})"
                ),

            "overall_elo_and_session_elo_change.txt":
                f"{overall_rating} ({overall_session_change})",

            # --------------------------------------------------
            # MONTHLY RATING
            # --------------------------------------------------

            "monthly_rank_label.txt":
                f"Rank: {season_rank_number}",

            "monthly_elo_and_rank_label.txt":
                (
                    f"Elo: {season_rating} "
                    f"(Rank: {season_rank_number})"
                ),

            "monthly_rank_hash.txt":
                season_rank_hash,

            "monthly_rank.txt":
                season_rank_number,

            "monthly_elo.txt":
                season_rating,

            "monthly_elo_label.txt":
                f"Elo: {season_rating}",

            # --------------------------------------------------
            # MONTHLY SESSION
            # --------------------------------------------------

            "monthly_session_elo_change_label.txt":
                f"Elo: {season_session_change}",

            "monthly_session_rank_change_label.txt":
                f"Rank: {season_session_rank_change}",

            "monthly_elo_and_session_elo_change_label.txt":
                (
                    f"Elo: {season_rating} "
                    f"({season_session_change})"
                ),

            "monthly_elo_and_session_elo_change.txt":
                f"{season_rating} ({season_session_change})",
        }

        if update_match_changes:

            output_files.update({

                # --------------------------------------------------
                # OVERALL LAST MATCH CHANGE
                # --------------------------------------------------

                "overall_elo_change.txt":
                    overall_change,

                "overall_elo_change_label.txt":
                    f"Elo: {overall_change}",

                "overall_elo_and_elo_change_label.txt":
                    (
                        f"Elo: {overall_rating} "
                        f"({overall_change})"
                    ),

                "overall_elo_and_elo_change.txt":
                    f"{overall_rating} ({overall_change})",

                "overall_rank_change.txt":
                    overall_rank_change,

                "overall_rank_change_label.txt":
                    f"Rank: {overall_rank_change}",

                # --------------------------------------------------
                # MONTHLY LAST MATCH CHANGE
                # --------------------------------------------------

                "monthly_elo_change.txt":
                    season_change,

                "monthly_elo_change_label.txt":
                    f"Elo: {season_change}",

                "monthly_elo_and_elo_change_label.txt":
                    (
                        f"Elo: {season_rating} "
                        f"({season_change})"
                    ),

                "monthly_elo_and_elo_change.txt":
                    f"{season_rating} ({season_change})",

                "monthly_rank_change.txt":
                    season_rank_change,

                "monthly_rank_change_label.txt":
                    f"Rank: {season_rank_change}",
            })

        update_trigger = datetime.now().isoformat()

        # Write all standard text output files.

        for filename, value in output_files.items():

            file_path = (
                self.output_directory
                / filename
            )

            with open(
                file_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(str(value))

        # --------------------------------------------------
        # JSON DATA
        # --------------------------------------------------

        json_data = {
            "player_id": player_id,
            "updated_at": update_trigger,
            "overall": overall,
            "season": season,
            "changes": changes,
        }

        json_path = (
            self.output_directory
            / "data.json"
        )

        with open(
            json_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                json_data,
                file,
                indent=4,
                ensure_ascii=False
            )

        # --------------------------------------------------
        # OUTPUT UPDATE TRIGGER
        #
        # This file is written last, after all output files
        # have been successfully updated.
        #
        # OBS Lua scripts can use this as a single shared
        # synchronization trigger.
        # --------------------------------------------------

        output_update_trigger = (
            self.output_directory
            / "output_update_trigger.txt"
        )

        with open(
            output_update_trigger,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                update_trigger
            )

        # --------------------------------------------------
        # MATCH UPDATE TRIGGER
        #
        # This file is only updated after a confirmed new match.
        #
        # It is used by OBS to trigger temporary overlays.
        # It must not change during the initial rating fetch
        # when the tool starts.
        # --------------------------------------------------

        if trigger_match_overlays:

            match_update_trigger = (
                self.output_directory
                / "match_update_trigger.txt"
            )

            with open(
                match_update_trigger,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    update_trigger
                )

    def format_change(self, value):
        """
        Format changes with an explicit sign.

        Undefined changes are displayed as N/A.
        """

        if value is None:
            return "N/A"

        if value >= 0:
            return f"+{value}"

        return str(value)


    def format_rank_number(self, rank):
        """
        Format a rank as a plain number.

        Players without a rank are displayed as Unranked.
        """

        if rank is None:
            return "Unranked"

        return str(rank)


    def format_rank_hash(self, rank):
        """
        Format a rank with a leading #.

        Players without a rank are displayed as Unranked.
        """

        if rank is None:
            return "Unranked"

        return f"#{rank}"