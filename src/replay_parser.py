import struct


REPLAY_HEADER_SIZE = 14
REPLAY_IDENTIFIER = b"GENREP"


def read_replay_header(replay_path):
    """
    Read the basic header information from a Generals replay.

    Returns:
        {
            "start_time": int,
            "end_time": int,
        }

    Raises:
        ValueError: If the file is not a valid or complete replay header.
        OSError: If the file cannot be read.
    """

    with open(
        replay_path,
        "rb"
    ) as file:

        header = file.read(
            REPLAY_HEADER_SIZE
        )


    if len(header) < REPLAY_HEADER_SIZE:

        raise ValueError(
            "Replay file header is incomplete."
        )


    if header[:6] != REPLAY_IDENTIFIER:

        raise ValueError(
            "Not a valid Generals replay file."
        )


    start_time = struct.unpack(
        "<I",
        header[6:10]
    )[0]


    end_time = struct.unpack(
        "<I",
        header[10:14]
    )[0]


    return {
        "start_time": start_time,
        "end_time": end_time,
    }