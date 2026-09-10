from pathlib import Path

from logger import log, log_block
from replay_parser import read_replay_metadata

GAME_INTERNET = 5
PLAYERTEMPLATE_OBSERVER = -2

class ReplayWatcher:
    def __init__(
        self,
        replay_directory,
        stop_event,
        on_game_end
    ):
        self.replay_directory = Path(
            replay_directory
        )
        self.stop_event = stop_event
        self.on_game_end = on_game_end

        self.replay_path = (
            self.replay_directory
            / "00000000.rep"
        )

        self.replay_start_time = None
        self.in_game = False
        self.game_eligible = False

    def run(self):
        """
        Monitor 00000000.rep for game starts and
        confirmed game ends.

        The watcher continues until stop_event is set.
        """

        if not self.replay_directory.exists():
            raise RuntimeError(
                f"Replays directory does not exist: "
                f"{self.replay_directory}"
            )

        log()
        log(
            "Monitoring 00000000.rep for game activity...",
            True
        )

        self._establish_baseline()

        while not self.stop_event.is_set():
            self._check_replay()

            if self.stop_event.wait(1):
                break

        log_block(
            [
                "Stopped replay monitoring."
            ]
        )

    def _establish_baseline(self):
        """
        Establish the current replay as the initial state.

        An existing active replay is treated as already in progress.
        Its eligibility is determined from the replay metadata.
        An existing completed replay is treated as already processed.
        """

        state = self._read_replay_state()

        if state is None:
            return

        start_time = state["start_time"]
        end_time = state["end_time"]

        if start_time == 0:
            return

        self.replay_start_time = start_time

        if end_time == 0:
            self.in_game = True
            self.game_eligible = self._is_game_eligible(state)

            log()
            log(
                "Active game detected."
            )
            self._log_game_eligibility()
            log(
                "Game monitoring started."
            )

    def _check_replay(self):
        state = self._read_replay_state()

        if state is None:
            return

        start_time = state["start_time"]
        end_time = state["end_time"]

        if start_time == 0:
            return

        # --------------------------------------------------
        # NEW REPLAY
        # --------------------------------------------------

        if (
            self.replay_start_time is None
            or start_time != self.replay_start_time
        ):
            self.replay_start_time = start_time
            self.game_eligible = self._is_game_eligible(state)

            if end_time == 0:
                self.in_game = True

                log(
                    "New game detected."
                )
                self._log_game_eligibility()
                log(
                    "Game monitoring started."
                )

            else:
                # A completed replay appeared without us seeing
                # its active state. Establish it as the baseline.
                self.in_game = False

            return

        # --------------------------------------------------
        # GAME END
        # --------------------------------------------------

        if (
            self.in_game
            and end_time != 0
        ):
            self.in_game = False
            game_eligible = self.game_eligible
            self.game_eligible = False

            log(
                "Game end detected."
            )

            if game_eligible:
                self.on_game_end()
            else:
                log(
                    "Rating update skipped. "
                    "Game is not eligible for a Strata rating update."
                )
            
            log()
            log(
                "Waiting for the next game..."
            )

    def _log_game_eligibility(self):
        if self.game_eligible:
            log(
                "Game is eligible for a Strata rating update."
            )
        else:
            log(
                "Game is not eligible for a Strata rating update. Strata API will not be called once the game ends."
            )

    def _read_replay_state(self):
        """
        Read the replay header and game metadata.

        Returns None if the replay is temporarily unavailable,
        incomplete, or invalid.
        """

        if not self.replay_path.exists():
            return None

        try:
            return read_replay_metadata(
                self.replay_path
            )

        except (
            OSError,
            ValueError
        ):
            return None
        
    def _is_game_eligible(self, state):
        if state["original_game_mode"] != 5:
            return False

        human_players_excluding_observers = [
            slot
            for slot in state["slots"]
            if slot["type"] == "human"
            and slot["player_template"] != -2
        ]

        ai_players = [
            slot
            for slot in state["slots"]
            if slot["type"] == "ai"
        ]

        if len(human_players_excluding_observers) != 2:
            return False

        if ai_players:
            return False

        player_1, player_2 = human_players_excluding_observers

        if (
            player_1["team_number"] >= 0
            and player_1["team_number"] == player_2["team_number"]
        ):
            return False

        return True