from pathlib import Path
import os
import sys


APP_NAME = "StrataStreamerTool"
APP_VERSION = "v1.0.0"

def get_application_directory():
    """
    Return the directory containing the application.

    During development, this is the project root.
    When packaged as an executable, this is the directory
    containing the executable.
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    return Path(__file__).resolve().parent.parent


def get_output_directory():
    """
    Return the directory used for generated OBS output files.
    """

    if getattr(sys, "frozen", False):
        local_appdata = os.getenv("LOCALAPPDATA")

        return (
            Path(local_appdata)
            / APP_NAME
            / "output"
        )

    return (
        get_application_directory()
        / "output"
    )


def get_appdata_directory():
    """
    Return the persistent application data directory.
    """

    appdata = os.getenv("APPDATA")

    return (
        Path(appdata)
        / APP_NAME
    )


def ensure_directories():
    """
    Create required application directories if they
    do not already exist.
    """

    get_output_directory().mkdir(
        parents=True,
        exist_ok=True
    )

    get_appdata_directory().mkdir(
        parents=True,
        exist_ok=True
    )