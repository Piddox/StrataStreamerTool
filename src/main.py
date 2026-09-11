import msvcrt
import threading
import time
from dataclasses import dataclass

from logger import log, log_block
from api import StrataAPI
from config import (
    get_or_create_config,
    get_selected_player,
    change_api_token
)
from app_paths import (
    get_output_directory,
    ensure_directories,
)

from updater import RatingUpdater
from writer import OutputWriter
from replay_watcher import ReplayWatcher

from app_paths import APP_VERSION

@dataclass
class MonitoringSession:

    player_id: int
    updater: RatingUpdater
    writer: OutputWriter
    stop_event: threading.Event
    watcher_thread: threading.Thread

def create_updater(api, player_id):
    """
    Create a RatingUpdater for the selected account.
    """

    return RatingUpdater(
        api,
        player_id,
    )

def create_writer():
    """
    Create the output writer.
    """

    return OutputWriter(
        get_output_directory()
    )

def fetch_initial_rating(updater, writer, is_account_switch=False):
    """
    Fetch and display the initial rating for the selected account, and write to output files.
    """

    log_block(
        [
            f"Fetching initial rating data for player {updater.player_id}..."
        ]
    )

    try:

        current_data = updater.fetch_rating_data()

        data, changes = (
            updater.process_rating_update(
                current_data
            )
        )

        writer.write_output_files(
            data,
            updater.player_id,
            changes,
            update_match_changes=is_account_switch,
            trigger_match_overlays=False
        )

    except Exception as error:

        log()
        log(f"ERROR: {error}")

        return False

    log("Initial update successful.", False)

    log(
        f"Overall Elo: "
        f"{data['overall']['rating']}", False
    )

    overall_rank = data["overall"].get("rank")

    if overall_rank is None:
        log("Overall Rank: Unranked", False)
    else:
        log(
            f"Overall Rank: "
            f"#{overall_rank}", False
        )

    log(
        f"Monthly Elo: "
        f"{data['season']['rating']}", False
    )

    season_rank = data["season"].get("rank")

    if season_rank is None:
        log("Monthly Rank: Unranked", False)
    else:
        log(
            f"Monthly Rank: "
            f"#{season_rank}", False
        )

    return True


def start_watcher(
    updater,
    writer,
    config,
    stop_event
):
    """
    Start the replay watcher in a background thread.
    """

    def on_game_end():
        updater.handle_game_end(
            stop_event,
            lambda data, changes, update_match_changes, trigger_match_overlays:
                handle_rating_update(
                    writer,
                    updater.player_id,
                    data,
                    changes,
                    update_match_changes,
                    trigger_match_overlays
                ),
            config.get(
                "rating_update_delay_seconds",
                1
            )
        )

    watcher = ReplayWatcher(
        replay_directory=config["replays_directory"],
        stop_event=stop_event,
        on_game_end=on_game_end
    )

    watcher_thread = threading.Thread(
        target=watcher.run,
        daemon=True
    )

    watcher_thread.start()

    return watcher_thread


def stop_watcher(
    stop_event,
    watcher_thread
):
    """
    Stop the replay watcher and wait for it to finish.
    """

    if stop_event is not None:

        stop_event.set()

    if (
        watcher_thread is not None
        and watcher_thread.is_alive()
    ):

        watcher_thread.join()

def show_commands():
    """
    Display the available keyboard commands.
    """

    log_block(
        [
            None,
            "Commands:",
            "[S] Switch to another linked GO account",
            "[C] Change API token",
            "[Q] Quit"
        ]
    )

def start_monitoring_session(
    api,
    config,
    force_account_selection=False,
    is_account_switch=False
):
    """
    Select a GO account, fetch its initial rating,
    and start replay monitoring.

    Returns: MonitoringSession(
        player_id=player_id,
        updater=updater,
        writer=writer,
        stop_event=stop_event,
        watcher_thread=watcher_thread
    )

    Returns None if the session could not be started.
    """

    try:

        player_id = get_selected_player(
            api,
            config,
            force_selection=force_account_selection
        )

    except RuntimeError as error:

        log()
        log(f"ERROR: {error}")

        return None

    log(
        f"Selected Player ID: "
        f"{player_id}", False
    )

    updater = create_updater(
        api,
        player_id
    )

    writer = create_writer()

    if not fetch_initial_rating(updater, writer, is_account_switch=is_account_switch):

        return None

    stop_event = threading.Event()

    watcher_thread = start_watcher(
        updater,
        writer,
        config,
        stop_event
    )

    return MonitoringSession(
        player_id=player_id,
        updater=updater,
        writer=writer,
        stop_event=stop_event,
        watcher_thread=watcher_thread
    )

def handle_rating_update(
    writer,
    player_id,
    data,
    changes,
    update_match_changes,
    trigger_match_overlays
):
    """
    Write updated rating data to the output files.
    """

    writer.write_output_files(
        data,
        player_id,
        changes,
        update_match_changes=update_match_changes,
        trigger_match_overlays=trigger_match_overlays
    )

def restart_monitoring_session(
    session,
    api,
    config,
    force_account_selection=True,
    is_account_switch=False
):
    """
    Stop the current monitoring session and start a new one.
    """

    stop_watcher(
        session.stop_event,
        session.watcher_thread
    )

    return start_monitoring_session(
        api,
        config,
        force_account_selection=force_account_selection,
        is_account_switch=is_account_switch
    )

def main():

    log_block(
        [
            "  ____  _____  ____      _   _____   _",
            " / ___||_   _||  _ \\    / \\ |_   _| / \\",
            " \\___ \\  | |  | |_) |  / _ \\  | |  / _ \\",
            "  ___) | | |  |  _  / / ___ \\ | | / ___ \\",
            " |____/  |_|  |_| \\_\\/_/   \\_\\|_|/_/   \\_\\",
            None,
            "         Strata Streamer Tool",
            "           Made by Piddox",
        ]
    )
    log("               "+APP_VERSION,False)
    log()

    ensure_directories()

    config = get_or_create_config()

    api = StrataAPI(
        config["api_token"]
    )

    session = start_monitoring_session(
        api,
        config
    )

    if session is None:
        return

    show_commands()

    try:

        while True:

            if msvcrt.kbhit():

                key = msvcrt.getwch().lower()

                if key == "q":

                    log()
                    log(
                        "Stopping Strata Streamer Tool..."
                    )

                    break

                if key == "s":

                    log()

                    log(
                        "Switching account...",
                        False
                    )

                    log()

                    session = restart_monitoring_session(
                        session,
                        api,
                        config,
                        force_account_selection=True,
                        is_account_switch=True
                    )

                    if session is None:
                        break

                    log_block(
                        [
                            None,
                            "Monitoring resumed."
                        ]
                    )

                    show_commands()

                if key == "c":

                    log()

                    log(
                        "Changing API token..."
                    )

                    try:

                        stop_watcher(
                            session.stop_event,
                            session.watcher_thread
                        )

                        config = change_api_token(
                            config
                        )

                    except RuntimeError as error:

                        log()

                        log(
                            f"ERROR: {error}"
                        )

                        break

                    api = StrataAPI(
                        config["api_token"]
                    )

                    log()

                    session = start_monitoring_session(
                        api,
                        config,
                        force_account_selection=True
                    )

                    if session is None:
                        break

                    log_block(
                        [
                            None,
                            "Monitoring resumed."
                        ]
                    )

                    show_commands()

            time.sleep(0.1)

    except KeyboardInterrupt:

        log()

        log(
            "Stopping Strata Streamer Tool..."
        )

    finally:

        stop_watcher(
            session.stop_event,
            session.watcher_thread
        )

        log()

        log("Strata Streamer Tool closed.")

if __name__ == "__main__":
    main()