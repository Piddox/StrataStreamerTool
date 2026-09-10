from pathlib import Path

from logger import log, log_block
from replay_parser import read_replay_header


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
                f"Stopped replay monitoring."
            ]
        )

    def _establish_baseline(self):
        """
        Establish the current replay as the initial state.

        An existing active replay is treated as already in progress.
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

            log()
            log(
                "Active game detected."
            )
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

            if end_time == 0:
                self.in_game = True

                log()
                log(
                    "New game detected."
                )
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

            log(
                "Game end detected."
            )

            self.on_game_end()

    def _read_replay_state(self):
        """
        Read the replay header.

        Returns None if the replay is temporarily unavailable,
        incomplete, or invalid.
        """

        if not self.replay_path.exists():
            return None

        try:
            return read_replay_header(
                self.replay_path
            )

        except (
            OSError,
            ValueError
        ):
            return None