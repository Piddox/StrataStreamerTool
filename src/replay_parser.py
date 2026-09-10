import struct


REPLAY_HEADER_SIZE = 14
REPLAY_IDENTIFIER = b"GENREP"

MAX_SLOTS = 8


class ReplayMetadataIncompleteError(ValueError):
    """Raised when the replay has not written enough metadata yet."""


def _read_ascii_string(file):
    """Read a null-terminated ASCII string."""

    value = bytearray()

    while True:
        byte = file.read(1)

        if not byte:
            raise ReplayMetadataIncompleteError(
                "Replay metadata is incomplete."
            )

        if byte == b"\x00":
            return value.decode("ascii", errors="replace")

        value.extend(byte)


def _read_unicode_string(file):
    """Read a null-terminated UTF-16LE string."""

    value = bytearray()

    while True:
        char = file.read(2)

        if len(char) < 2:
            raise ReplayMetadataIncompleteError(
                "Replay metadata is incomplete."
            )

        if char == b"\x00\x00":
            try:
                return value.decode("utf-16-le")
            except UnicodeDecodeError as error:
                raise ValueError(
                    "Replay contains invalid Unicode metadata."
                ) from error

        value.extend(char)


def _parse_game_options(game_options):
    """Parse the serialized GameInfo slot list."""

    slot_list = None

    for option in game_options.split(";"):
        if option.startswith("S="):
            slot_list = option[2:]
            break

    if slot_list is None:
        raise ValueError(
            "Replay GameInfo does not contain a slot list."
        )

    slots = []

    for slot_index, raw_slot in enumerate(slot_list.split(":")):
        if not raw_slot:
            continue

        if raw_slot.startswith("H"):
            fields = raw_slot.split(",")

            if len(fields) < 9:
                raise ValueError(
                    "Replay contains an invalid human slot."
                )

            try:
                player_template = int(fields[-4])
                start_position = int(fields[-3])
                team_number = int(fields[-2])
                nat_behavior = int(fields[-1])
            except ValueError as error:
                raise ValueError(
                    "Replay contains invalid human slot data."
                ) from error

            slots.append({
                "slot": slot_index,
                "type": "human",
                "player_template": player_template,
                "start_position": start_position,
                "team_number": team_number,
                "nat_behavior": nat_behavior,
            })

        elif raw_slot.startswith("C"):
            fields = raw_slot.split(",")

            if len(fields) != 5:
                raise ValueError(
                    "Replay contains an invalid AI slot."
                )

            try:
                player_template = int(fields[2])
                start_position = int(fields[3])
                team_number = int(fields[4])
            except ValueError as error:
                raise ValueError(
                    "Replay contains invalid AI slot data."
                ) from error

            slots.append({
                "slot": slot_index,
                "type": "ai",
                "difficulty": fields[0][1:],
                "player_template": player_template,
                "start_position": start_position,
                "team_number": team_number,
            })

        elif raw_slot == "O":
            slots.append({
                "slot": slot_index,
                "type": "open",
            })

        elif raw_slot == "X":
            slots.append({
                "slot": slot_index,
                "type": "closed",
            })

        else:
            raise ValueError(
                "Replay contains an invalid slot entry."
            )

    return slots


def read_replay_metadata(replay_path):
    """
    Read and expose replay metadata from a Generals replay.

    Returns a dictionary containing the replay header,
    metadata, GameInfo options, and slot information.

    Raises:
        ValueError: If the replay is invalid or its metadata
            is incomplete.
        OSError: If the file cannot be read.
    """

    with open(replay_path, "rb") as file:
        header = file.read(REPLAY_HEADER_SIZE)

        if len(header) < REPLAY_HEADER_SIZE:
            raise ReplayMetadataIncompleteError(
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

        # Frame count, desync flag, quit flag,
        # and player disconnect flags.
        fixed_header = file.read(14)

        if len(fixed_header) < 14:
            raise ReplayMetadataIncompleteError(
                "Replay file header is incomplete."
            )

        frame_count = struct.unpack(
            "<I",
            fixed_header[0:4]
        )[0]

        desync_game = fixed_header[4] != 0
        quit_early = fixed_header[5] != 0

        player_disconnections = list(
            fixed_header[6:14]
        )

        replay_name = _read_unicode_string(file)

        system_time = file.read(16)

        if len(system_time) < 16:
            raise ReplayMetadataIncompleteError(
                "Replay metadata is incomplete."
            )

        version_string = _read_unicode_string(file)
        version_time_string = _read_unicode_string(file)

        fixed_metadata = file.read(12)

        if len(fixed_metadata) < 12:
            raise ReplayMetadataIncompleteError(
                "Replay metadata is incomplete."
            )

        version_number = struct.unpack(
            "<I",
            fixed_metadata[0:4]
        )[0]

        version_crc = struct.unpack(
            "<I",
            fixed_metadata[4:8]
        )[0]

        executable_crc = struct.unpack(
            "<I",
            fixed_metadata[8:12]
        )[0]

        game_options = _read_ascii_string(file)

        slots = _parse_game_options(game_options)

        local_player_index = int(
            _read_ascii_string(file)
        )

        difficulty = _read_uint32(file)
        
        original_game_mode = _read_int32(file)

        rank_points = _read_uint32(file)
        
        max_fps = _read_uint32(file)

    return {
        "start_time": start_time,
        "end_time": end_time,
        "frame_count": frame_count,
        "desync_game": desync_game,
        "quit_early": quit_early,
        "player_disconnections": player_disconnections,

        "replay_name": replay_name,
        "system_time": system_time,
        "version_string": version_string,
        "version_time_string": version_time_string,
        "version_number": version_number,
        "version_crc": version_crc,
        "executable_crc": executable_crc,

        "game_options": game_options,
        "slots": slots,

        "local_player_index": local_player_index,
        "difficulty": difficulty,
        "original_game_mode": original_game_mode,
        "rank_points": rank_points,
        "max_fps": max_fps,
    }

def _read_uint32(file):
    data = file.read(4)

    if len(data) < 4:
        raise ReplayMetadataIncompleteError(
            "Replay metadata is incomplete."
        )

    return struct.unpack("<I", data)[0]

def _read_int32(file):
    data = file.read(4)

    if len(data) < 4:
        raise ReplayMetadataIncompleteError(
            "Replay metadata is incomplete."
        )

    return struct.unpack("<i", data)[0]