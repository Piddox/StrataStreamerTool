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

    def _get_existing_match_update_trigger(self):
        json_path = self.output_directory / "data.json"

        try:
            with open(
                json_path,
                "r",
                encoding="utf-8"
            ) as file:
                existing_data = json.load(file)

            return existing_data.get(
                "match_update_trigger"
            )

        except (
            OSError,
            json.JSONDecodeError
        ):
            return None

    def write_game_start(self, local_player_template):
        """
        Update data.json with the local player's faction
        detected at game start.
        """

        json_path = (
            self.output_directory
            / "data.json"
        )

        # Read the existing JSON data so all existing rating
        # information is preserved.
        with open(
            json_path,
            "r",
            encoding="utf-8"
        ) as file:

            json_data = json.load(file)

        # Store the local player's faction.
        json_data["local_player_faction"] = (
            self._get_faction_name(local_player_template)
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

    def _get_faction_name(self, player_template):
        faction_names = {
            1: "Observer",
            2: "USA",
            3: "China",
            4: "GLA",
            5: "USA",
            6: "USA",
            7: "USA",
            8: "China",
            9: "China",
            10: "China",
            11: "GLA",
            12: "GLA",
            13: "GLA"
        }

        return faction_names.get(
            player_template,
            "Unknown"
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
        monthly = data["season"]

        overall_rating = overall.get("rating")
        overall_rank = overall.get("rank")

        monthly_rating = monthly.get("rating")
        monthly_rank = monthly.get("rank")

        overall_rank_change = self.format_change(
            changes["overall_rank_change"]
        )

        monthly_rank_change = self.format_change(
            changes["monthly_rank_change"]
        )

        overall_session_change = self.format_change(
            changes["overall_session_rating_change"]
        )

        overall_session_rank_change = self.format_change(
            changes["overall_session_rank_change"]
        )

        monthly_session_change = self.format_change(
            changes["monthly_session_rating_change"]
        )

        monthly_session_rank_change = self.format_change(
            changes["monthly_session_rank_change"]
        )

        overall_change = self.format_change(
            changes["overall_rating_change"]
        )

        monthly_change = self.format_change(
            changes["monthly_rating_change"]
        )

        overall_rank_number = self.format_rank_number(
            overall_rank
        )

        overall_rank_hash = self.format_rank_hash(
            overall_rank
        )

        monthly_rank_number = self.format_rank_number(
            monthly_rank
        )

        monthly_rank_hash = self.format_rank_hash(
            monthly_rank
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
                f"Rank: {monthly_rank_number}",

            "monthly_elo_and_rank_label.txt":
                (
                    f"Elo: {monthly_rating} "
                    f"(Rank: {monthly_rank_number})"
                ),

            "monthly_rank_hash.txt":
                monthly_rank_hash,

            "monthly_rank.txt":
                monthly_rank_number,

            "monthly_elo.txt":
                monthly_rating,

            "monthly_elo_label.txt":
                f"Elo: {monthly_rating}",

            # --------------------------------------------------
            # MONTHLY SESSION
            # --------------------------------------------------

            "monthly_session_elo_change_label.txt":
                f"Elo: {monthly_session_change}",

            "monthly_session_rank_change_label.txt":
                f"Rank: {monthly_session_rank_change}",

            "monthly_elo_and_session_elo_change_label.txt":
                (
                    f"Elo: {monthly_rating} "
                    f"({monthly_session_change})"
                ),

            "monthly_elo_and_session_elo_change.txt":
                f"{monthly_rating} ({monthly_session_change})",
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
                    monthly_change,

                "monthly_elo_change_label.txt":
                    f"Elo: {monthly_change}",

                "monthly_elo_and_elo_change_label.txt":
                    (
                        f"Elo: {monthly_rating} "
                        f"({monthly_change})"
                    ),

                "monthly_elo_and_elo_change.txt":
                    f"{monthly_rating} ({monthly_change})",

                "monthly_rank_change.txt":
                    monthly_rank_change,

                "monthly_rank_change_label.txt":
                    f"Rank: {monthly_rank_change}",
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

        existing_match_update_trigger = (
            self._get_existing_match_update_trigger()
        )

        if trigger_match_overlays:
            match_update_trigger = update_trigger
        else:
            match_update_trigger = existing_match_update_trigger

        json_data = {
            "player_id": player_id,
            "updated_at": update_trigger,
            "match_update_trigger": match_update_trigger,
            "overall": overall,
            "monthly": monthly,
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

    def write_game_end(self):
        """
        Remove the local player's faction from data.json
        when the game ends and the overlay returns to menu state.
        """

        json_path = (
            self.output_directory
            / "data.json"
        )

        # Read the existing JSON data so all existing rating
        # information is preserved.
        with open(
            json_path,
            "r",
            encoding="utf-8"
        ) as file:

            json_data = json.load(file)

        # The local faction is only valid while in-game.
        json_data.pop(
            "local_player_faction",
            None
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