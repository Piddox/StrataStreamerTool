"""Overlay configuration and static definitions."""

HOST = "127.0.0.1"
PORT = 1337


SUPPORTED_RESOLUTIONS = {
    1920: {
        "width": 1920,
        "height": 1080
    },
    2560: {
        "width": 2560,
        "height": 1440
    }
}

DEFAULT_OVERLAY_CONFIG = {
    "resolution": 2560,

    "hud_1": {
        "visibility_mode": "always",
        "hide_when_observing": False,
        "template": "rating_rank",
        "ladder": "monthly",
        "artwork_size": "small",
        "artwork_color": "faction_dependent",
        "position_mode": "automatic",
        "in_game_position": "hud_left",
        "in_menu_position": "right_top"
    },

    "hud_2": {
        "visibility_mode": "always",
        "hide_when_observing": False,
        "template": "session",
        "ladder": "monthly",
        "artwork_size": "big",
        "artwork_color": "faction_dependent",
        "position_mode": "automatic",
        "in_game_position": "hud_right",
        "in_menu_position": "right_middle"
    }
}

IN_GAME_POSITIONS = [
    "left_top",
    "left_middle",
    "left_bottom",
    "right_top",
    "right_middle",
    "right_bottom",
    "hud_left",
    "hud_right"
]


IN_MENU_POSITIONS = [
    "left_top",
    "left_middle",
    "left_bottom",
    "right_top",
    "right_middle",
    "right_bottom"
]


VISIBILITY_MODES = [
    "never",
    "in_game",
    "in_menu",
    "always"
]

POSITION_MODES = [
    "in_game",
    "in_menu",
    "automatic"
]


TEMPLATES = {
    "rating_rank": {
        "name": "Rating + Rank",
        "description": "Player rating and rank."
    },
    "session": {
        "name": "Session",
        "description": "Current session rating and rank changes."
    }
}

ARTWORK_SIZES = {
    "small": {
        "name": "Small",
        "description": "Small HUD artwork."
    },
    "big": {
        "name": "Big",
        "description": "Large HUD artwork."
    }
}

ARTWORK_COLORS = {
    "faction_dependent": {
        "name": "Faction-dependent",
        "description": "Automatically switches artwork based on the player's faction."
    },
    "blue": {
        "name": "Blue (USA)",
        "description": "Always use USA artwork."
    },
    "red": {
        "name": "Red (China)",
        "description": "Always use China artwork."
    },
    "green": {
        "name": "Green (GLA)",
        "description": "Always use GLA artwork."
    }
}

LADDERS = {
    "overall": {
        "name": "Overall",
        "description": "Overall ladder rating and rank."
    },
    "monthly": {
        "name": "Monthly",
        "description": "Current monthly rating and rank."
    }
}