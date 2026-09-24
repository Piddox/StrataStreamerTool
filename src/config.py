import copy
import json
from pathlib import Path
import msvcrt

from api import (
    StrataAPI,
    NoLinkedPlayersError,
)
from app_paths import get_appdata_directory, get_output_directory
from overlay_config import DEFAULT_OVERLAY_CONFIG

CONFIG_DIRECTORY = (
    get_appdata_directory()
)

OUTPUT_DIRECTORY = (
    get_output_directory()
)

CONFIG_PATH = (
    CONFIG_DIRECTORY
    / "config.json"
)


DEFAULT_CONFIG = {
    "api_token": "",
    "replays_directory": "",
    "rating_update_delay_seconds": 0,
    "selected_player_id": None,
    "overlay": copy.deepcopy(DEFAULT_OVERLAY_CONFIG)
}

def get_default_config():
    """Return a fresh copy of the default configuration."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["overlay"] = copy.deepcopy(DEFAULT_OVERLAY_CONFIG)
    return config

def ensure_config_directory():
    """
    Create the application configuration directory
    if it does not already exist.
    """

    CONFIG_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )


def load_config():
    """
    Load the configuration file.

    Returns the configuration dictionary, or None
    if no configuration file exists.
    """

    if not CONFIG_PATH.exists():
        return None

    try:
        with open(
            CONFIG_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            config = json.load(file)

            migrated = False

            if "overlay" not in config:
                config["overlay"] = copy.deepcopy(
                    DEFAULT_OVERLAY_CONFIG
                )
                migrated = True

            if migrated:
                save_config(config)

            return config

    except (
        OSError,
        json.JSONDecodeError
    ) as error:

        raise RuntimeError(
            f"Could not load configuration: {error}"
        ) from error


def save_config(config):
    """
    Save the configuration dictionary.
    """

    ensure_config_directory()

    try:
        with open(
            CONFIG_PATH,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                config,
                file,
                indent=4,
                ensure_ascii=False
            )

    except OSError as error:
        raise RuntimeError(
            f"Could not save configuration: {error}"
        ) from error


def save_overlay_config(config, overlay_config):
    """
    Update and save the overlay configuration.
    """

    updated_config = copy.deepcopy(config)
    updated_config["overlay"] = copy.deepcopy(
        overlay_config
    )

    save_config(updated_config)

    config["overlay"] = copy.deepcopy(
        overlay_config
    )

def save_selected_player(
    config,
    player_id
):
    """
    Save the currently selected GO account.
    """

    config["selected_player_id"] = player_id

    save_config(config)


def configuration_is_complete(config):
    """
    Check whether all required configuration values exist.
    """

    required_fields = [
        "api_token",
        "replays_directory"
    ]

    for field in required_fields:

        value = config.get(field)

        if value is None or value == "":
            return False

    return True

def get_selected_player(
    api,
    config,
    force_selection=False
):
    """
    Return the selected GO account.

    If exactly one GO account is linked, select it automatically.
    Otherwise, use the previously selected account when possible,
    or show the account selection menu.
    """

    player_ids = api.get_available_players()

    if not player_ids:

        raise RuntimeError(
            "No linked GO accounts were found."
        )

    # If only one account is linked, select it automatically.
    if len(player_ids) == 1:

        selected_player_id = player_ids[0]

        save_selected_player(
            config,
            selected_player_id
        )

        return selected_player_id

    saved_player_id = config.get(
        "selected_player_id"
    )

    # Use the saved account automatically if it is still valid.
    if (
        not force_selection
        and saved_player_id is not None
        and int(saved_player_id) in player_ids
    ):

        return int(saved_player_id)

    # Saved account no longer exists.
    if (
        saved_player_id is not None
        and not force_selection
    ):

        print()
        print(
            "Previously selected GO account is no longer "
            "linked to this Strata account."
        )

    # Show account selection.
    print("Available GO accounts:")
    print()

    for index, player_id in enumerate(
        player_ids,
        start=1
    ):

        print(
            f"{index}. Player ID: {player_id}"
        )

    while True:

        print()

        selection = input(
            f"Select account [1-{len(player_ids)}]: "
        ).strip()

        try:

            selection_number = int(selection)

            if (
                1
                <= selection_number
                <= len(player_ids)
            ):

                selected_player_id = (
                    player_ids[
                        selection_number - 1
                    ]
                )

                save_selected_player(
                    config,
                    selected_player_id
                )

                print()
                return selected_player_id

        except ValueError:
            pass

        print(
            "Invalid selection. Please try again."
        )

def run_setup_wizard():
    """
    Run the first-time configuration wizard.
    """

    print_setup_header()

    config = get_default_config()

    api_token = prompt_for_api_token()

    print()
    print("Your output directory is:")
    print(
        OUTPUT_DIRECTORY
    )
    print("You can find all the text sources to be used in OBS here.")

    replays_directory = (
        prompt_for_replays_directory()
    )

    config["api_token"] = api_token

    config["replays_directory"] = (
        replays_directory
    )

    save_config(config)

    print()
    print(
        "Configuration saved successfully."
    )

    print(
        f"Config location: {CONFIG_PATH}"
    )
    print()

    return config

def print_setup_header():
    """
    Display the setup wizard header.
    """

    print()
    print("====================================")
    print("   STRATA STREAMER TOOL - SETUP")
    print("====================================")

def prompt_for_api_token():
    """
    Prompt the user for a Strata API token and validate it.

    The token is accepted only when it is valid and the
    associated Strata account has at least one linked GO account.

    Returns the validated API token.
    """

    while True:

        print()

        token = prompt_hidden_input(
            "Enter your Strata API token and hit Enter: "
        ).strip()

        if not token:

            print()
            print(
                "API token cannot be empty."
            )

            continue

        print()
        print(
            "Validating API token..."
        )

        api = StrataAPI(token)

        try:

            players = api.get_available_players()

        except NoLinkedPlayersError:

            print()
            print(
                "This Strata account does not have any "
                "GO accounts linked to it."
            )

            print(
                "Please link your Generals Online account "
                "to your Strata account and try again."
            )

            continue

        except RuntimeError as error:

            print()
            print(
                f"API token validation failed: {error}"
            )

            print(
                "Please check your token and try again."
            )

            continue

        print(
            "API token validated successfully."
        )

        print()
        if len(players) == 1:
            print(
                f"Found 1 linked GO account."
            )
        else:
             print(
                f"Found {len(players)} linked GO accounts."
            )

        return token

def prompt_hidden_input(prompt):
    """
    Prompt for sensitive input while displaying asterisks
    instead of the actual characters.
    """

    print(prompt, end="", flush=True)

    value = []

    while True:

        char = msvcrt.getwch()

        if char in ("\r", "\n"):

            print()
            break

        if char == "\003":

            raise KeyboardInterrupt

        if char == "\b":

            if value:

                value.pop()

                print(
                    "\b \b",
                    end="",
                    flush=True
                )

            continue

        value.append(char)

        print(
            "*",
            end="",
            flush=True
        )

    return "".join(value)

def prompt_for_replays_directory():
    """
    Prompt the user for the Zero Hour Replays directory.

    The directory must exist and contain 00000000.rep.

    Returns the validated directory path as a string.
    """

    while True:

        print()

        replays_directory = input(
            "Enter your Zero Hour Replays directory: "
        ).strip()

        replays_path = Path(
            replays_directory
        )

        if not replays_path.exists():

            print()
            print(
                "Directory not found."
            )

            print(
                "Please check the path and try again."
            )

            continue

        if not replays_path.is_dir():

            print()
            print(
                "The specified path is not a directory."
            )

            print(
                "Please enter your Zero Hour Replays directory."
            )

            continue

        replay_file = (
            replays_path / "00000000.rep"
        )

        if not replay_file.exists():

            print()
            print(
                "00000000.rep was not found in this directory."
            )

            print(
                "Please make sure you selected the correct "
                "Zero Hour Replays directory."
            )

            continue

        return str(replays_path)

def get_or_create_config():
    """
    Load the existing configuration.

    If configuration is missing or incomplete,
    run the setup wizard.
    """

    config = load_config()

    if config is None:

        print("No configuration found.")
        print("Starting first-time setup...")

        return run_setup_wizard()

    if not configuration_is_complete(config):

        print(
            "Configuration is incomplete."
        )
        print("Starting setup...")

        return run_setup_wizard()

    print("Loading previous configuration...")

    return config

def change_api_token(config):
    """
    Prompt the user for a new API token and update
    the saved configuration.

    Returns the updated configuration.
    """

    print()
    print(
        "-----------------------"
    )
    print(
        "CHANGE STRATA API TOKEN"
    )

    print(
        "-----------------------"
    )

    new_token = prompt_for_api_token()

    config["api_token"] = new_token

    save_config(config)

    print()
    print(
        "API token updated successfully."
    )

    return config