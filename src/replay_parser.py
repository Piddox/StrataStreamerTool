import struct


REPLAY_HEADER_SIZE = 14
REPLAY_IDENTIFIER = b"GENREP"

MAX_SLOTS = 8


# Generals uses this RNG when resolving random player templates.
# This is a local replay-specific RNG state; it is reinitialized for
# every replay parse so repeated metadata reads cannot leak RNG state.
GAME_LOGIC_SEED = [
    0xF22D0E56,
    0x883126E9,
    0xC624DD2F,
    0x0702C49C,
    0x9E353F7D,
    0x6FDF3B64,
]

AVAILABLE_TEMPLATES = {
    1: "Observer",
    2: "USA",
    3: "China",
    4: "GLA",
    5: "USA: Super Weapon",
    6: "USA: Laser",
    7: "USA: Air Force",
    8: "China: Tank",
    9: "China: Infantry",
    10: "China: Nuke",
    11: "GLA: Toxin",
    12: "GLA: Demolition",
    13: "GLA: Stealth",
}

AVAILABLE_COLORS = {
    0: "Yellow",
    1: "Red",
    2: "Blue",
    3: "Green",
    4: "Orange",
    5: "Cyan",
    6: "Purple",
    7: "Pink",
}


def _extract_seed_from_options(game_options):
    """Extract the replay's game-logic random seed from SD=."""
    for option in game_options.split(";"):
        option = option.strip()
        if option.startswith("SD="):
            try:
                return int(option[3:])
            except ValueError:
                return None
    return None


def _seed_random(seed):
    """Initialize a fresh copy of the Generals game-logic RNG state."""
    state = GAME_LOGIC_SEED.copy()
    state[0] = (seed + 0xF22D0E56) & 0xFFFFFFFF
    state[1] = (state[0] + (0x883126E9 - 0xF22D0E56)) & 0xFFFFFFFF
    state[2] = (state[1] + (0xC624DD2F - 0x883126E9)) & 0xFFFFFFFF
    state[3] = (state[2] + (0x0702C49C - 0xC624DD2F)) & 0xFFFFFFFF
    state[4] = (state[3] + (0x9E353F7D - 0x0702C49C)) & 0xFFFFFFFF
    state[5] = (state[4] + (0x6FDF3B64 - 0x9E353F7D)) & 0xFFFFFFFF
    return state


def _adc(a, b, carry):
    total = a + b + carry
    return total & 0xFFFFFFFF, total >> 32


def _random_value(state):
    """Generate one value using the Generals game-logic RNG."""
    carry = 0

    value, carry = _adc(state[5], state[4], carry)
    state[4] = value
    value, carry = _adc(value, state[3], carry)
    state[3] = value
    value, carry = _adc(value, state[2], carry)
    state[2] = value
    value, carry = _adc(value, state[1], carry)
    state[1] = value
    value, carry = _adc(value, state[0], carry)
    state[0] = value

    state[5] = (state[5] + 1) & 0xFFFFFFFF
    if state[5] == 0:
        state[4] = (state[4] + 1) & 0xFFFFFFFF
        if state[4] == 0:
            state[3] = (state[3] + 1) & 0xFFFFFFFF
            if state[3] == 0:
                state[2] = (state[2] + 1) & 0xFFFFFFFF
                if state[2] == 0:
                    state[1] = (state[1] + 1) & 0xFFFFFFFF
                    if state[1] == 0:
                        state[0] = (state[0] + 1) & 0xFFFFFFFF
                        value = (value + 1) & 0xFFFFFFFF

    return value


def _game_logic_random_value(state, lo, hi):
    delta = hi - lo + 1
    if delta == 0:
        return hi
    return (_random_value(state) % delta) + lo


def _resolve_random_templates(slots, game_options):
    """
    Resolve random player templates (-1) to the actual template selected
    by Generals.

    The raw player_template value is preserved. The resolved value is
    stored separately so observer detection can continue to use the raw
    -2 value.
    """
    seed = _extract_seed_from_options(game_options)
    if seed is None:
        return

    rng = _seed_random(seed)
    valid_templates = list(range(2, 14))
    taken_colors = set()

    for slot in slots:
        if slot["type"] not in ("human", "ai"):
            continue

        raw_template = slot["player_template"]

        if raw_template == -2:
            # Raw replay value -2 means observer. The resolved template
            # representation used by the game/parser is template 1.
            resolved_template = 1
        elif raw_template == -1:
            # This apparently pointless seed-dependent discard is part of
            # the game's random-template selection sequence.
            for _ in range(seed % 7):
                _game_logic_random_value(rng, 0, 1)

            index = (
                _game_logic_random_value(rng, 0, 1000)
                % len(valid_templates)
            )
            resolved_template = valid_templates[index]
        elif raw_template in AVAILABLE_TEMPLATES:
            resolved_template = raw_template
        else:
            # Match the third-party parser's fallback for an invalid
            # template value.
            for _ in range(seed % 7):
                _game_logic_random_value(rng, 0, 1)

            index = (
                _game_logic_random_value(rng, 0, 1000)
                % len(valid_templates)
            )
            resolved_template = valid_templates[index]

        slot["resolved_player_template"] = resolved_template

        # Colors are not currently needed by Strata, but random color
        # selection consumes the same RNG. Reproduce that consumption so
        # a later random player's template is resolved at the right point
        # in the RNG sequence.
        if slot["type"] == "human":
            raw_color = slot.get("color", -1)
        else:
            raw_color = slot.get("color", -1)

        if raw_color == -1:
            color_index = _game_logic_random_value(
                rng, 0, len(AVAILABLE_COLORS) - 1
            )
            while color_index in taken_colors:
                color_index = _game_logic_random_value(
                    rng, 0, len(AVAILABLE_COLORS) - 1
                )
        elif raw_color in AVAILABLE_COLORS:
            color_index = raw_color
        else:
            color_index = _game_logic_random_value(
                rng, 0, len(AVAILABLE_COLORS) - 1
            )

        taken_colors.add(color_index)


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
                color = int(fields[-5])
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
                "color": color,
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
                color = int(fields[1])
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
                "color": color,
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

        _resolve_random_templates(slots, game_options)

        local_player_index = int(
            _read_ascii_string(file)
        )

        local_player = next(
            (
                slot
                for slot in slots
                if slot["slot"] == local_player_index
            ),
            None
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
        "local_player": local_player,
        "local_player_template": (
            local_player.get("resolved_player_template")
            if local_player is not None
            else None
        ),
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