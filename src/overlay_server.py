"""Local HTTP server for the Strata Browser Source overlay."""

import copy
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from urllib.parse import urlparse
from datetime import datetime

from app_paths import get_output_directory
from config import save_overlay_config
from overlay_config import (
    HOST,
    PORT,
    IN_GAME_POSITIONS,
    IN_MENU_POSITIONS,
    VISIBILITY_MODES,
    POSITION_MODES,
    TEMPLATES,
    ARTWORK_SIZES,
    ARTWORK_COLORS,
    LADDERS
)
from overlay_data import TEST_DATA, TEST_DATA_STATES

if getattr(sys, "frozen", False):
    OVERLAY_DIRECTORY = Path(sys._MEIPASS) / "overlay"
else:
    OVERLAY_DIRECTORY = Path(__file__).resolve().parent.parent / "overlay"
READY_FILE = Path(os.environ.get("TEMP", Path.cwd())) / "StrataStreamerTool.ready"
HEARTBEAT_INTERVAL = 1.0


ENABLE_TEST_MODE = False

# Raised while sending a response when the browser has gone away, for
# example because it no longer needs an artwork file it already asked
# for, or because the overlay page was closed or reloaded.
CLIENT_DISCONNECT_ERRORS = (
    ConnectionAbortedError,
    ConnectionResetError,
    BrokenPipeError
)

# The artwork files only change when the application itself is updated.
# Serving them as no-store forces a full download of every image on
# every artwork change, which is both wasteful and long enough to be
# cancelled halfway through. They are cached and revalidated instead.
STATIC_ASSET_CACHE_CONTROL = "max-age=3600"

TEST_POSITION_COMBINATIONS = [
    ("hud_left", "hud_right"),
    ("left_top", "right_top"),
    ("left_middle", "right_middle"),
    ("left_bottom", "right_bottom"),
    ("left_top", "left_middle"),
    ("left_middle", "left_bottom"),
    ("right_bottom", "right_middle"),
    ("right_middle", "right_top"),
]

TEST_MENU_POSITION_COMBINATIONS = [
    ("left_top", "left_middle"),
    ("left_middle", "left_bottom"),
    ("left_bottom", "right_bottom"),
    ("right_bottom", "right_middle"),
    ("right_middle", "right_top"),
    ("left_top", "right_top"),
    ("left_middle", "right_middle"),
]

class _OverlayRequestHandler(BaseHTTPRequestHandler):
    server_version = "StrataStreamerOverlay/1.0"

    def log_message(self, format_string, *args):
        return

    def _send_response(
        self,
        status_code,
        content_type,
        body,
        cache_control="no-store",
        etag=None
    ):
        if isinstance(body, str): body = body.encode("utf-8")

        try:
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", cache_control)

            if etag is not None:
                self.send_header("ETag", etag)

            self.end_headers()
            self.wfile.write(body)

        except CLIENT_DISCONNECT_ERRORS:
            # The client cancelled this request. There is nothing left
            # to send and nothing worth reporting.
            self.close_connection = True

    def _send_not_modified(self, etag):
        try:
            self.send_response(304)
            self.send_header("Cache-Control", STATIC_ASSET_CACHE_CONTROL)
            self.send_header("ETag", etag)
            self.end_headers()

        except CLIENT_DISCONNECT_ERRORS:
            self.close_connection = True

    def _get_asset_etag(self, asset_path):
        asset_stat = asset_path.stat()

        return '"%x-%x"' % (
            asset_stat.st_size,
            asset_stat.st_mtime_ns
        )

    def _send_json(self, data):
        self._send_response(200, "application/json; charset=utf-8", json.dumps(data, ensure_ascii=False))

    def _send_overlay_file(self, filename, content_type):
        try: body = (OVERLAY_DIRECTORY / filename).read_bytes()
        except OSError: self._send_response(500, "text/plain; charset=utf-8", "Overlay asset could not be loaded"); return
        self._send_response(200, content_type, body)

    def _send_overlay_asset(self, relative_path, content_type):
        asset_path = OVERLAY_DIRECTORY / relative_path

        try:
            etag = self._get_asset_etag(asset_path)
        except OSError:
            self._send_response(
                404,
                "text/plain; charset=utf-8",
                "Overlay asset not found"
            )
            return

        if self.headers.get("If-None-Match") == etag:
            self._send_not_modified(etag)
            return

        try:
            body = asset_path.read_bytes()
        except OSError:
            self._send_response(
                404,
                "text/plain; charset=utf-8",
                "Overlay asset not found"
            )
            return

        self._send_response(
            200,
            content_type,
            body,
            cache_control=STATIC_ASSET_CACHE_CONTROL,
            etag=etag
        )

    def do_POST(self):
        path = urlparse(self.path).path

        if path != "/config":
            self._send_response(
                404,
                "text/plain; charset=utf-8",
                "Not found"
            )
            return

        try:
            content_length = int(
                self.headers.get("Content-Length", 0)
            )

            body = self.rfile.read(content_length)

            overlay_config = json.loads(
                body.decode("utf-8")
            )

            self.server.update_overlay_config(
                overlay_config
            )

            self._send_json(
                self.server.get_overlay_config()
            )

        except json.JSONDecodeError as error:
            self._send_response(
                400,
                "application/json; charset=utf-8",
                json.dumps({"error": str(error)})
            )
        except ValueError as error:
            self._send_response(
                400,
                "application/json; charset=utf-8",
                json.dumps({"error": str(error)})
            )
        except RuntimeError as error:
            self._send_response(
                500,
                "application/json; charset=utf-8",
                json.dumps({"error": str(error)})
            )

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/settings":
            self._send_overlay_file(
                "settings.html",
                "text/html; charset=utf-8"
            )
            return

        if path == "/overlay/settings.css":
            self._send_overlay_file(
                "settings.css",
                "text/css; charset=utf-8"
            )
            return

        if path == "/overlay/settings.js":
            self._send_overlay_file(
                "settings.js",
                "application/javascript; charset=utf-8"
            )
            return

        if path in ("/", "/overlay"):
            self._send_overlay_file(
                "index.html",
                "text/html; charset=utf-8"
            )
            return

        if path == "/overlay/style.css":
            self._send_overlay_file(
                "style.css",
                "text/css; charset=utf-8"
            )
            return

        if path == "/overlay/overlay.js":
            self._send_overlay_file(
                "overlay.js",
                "application/javascript; charset=utf-8"
            )
            return

        if path == "/overlay/overlay_data.js":
            self._send_overlay_file(
                "overlay_data.js",
                "application/javascript; charset=utf-8"
            )
            return

        if path == "/overlay/artwork/china_small.png":
            self._send_overlay_asset(
                "artwork/china_small.png",
                "image/png"
            )
            return

        if path == "/overlay/artwork/china_big.png":
            self._send_overlay_asset(
                "artwork/china_big.png",
                "image/png"
            )
            return

        if path == "/overlay/artwork/gla_small.png":
            self._send_overlay_asset(
                "artwork/gla_small.png",
                "image/png"
            )
            return

        if path == "/overlay/artwork/gla_big.png":
            self._send_overlay_asset(
                "artwork/gla_big.png",
                "image/png"
            )
            return

        if path == "/overlay/artwork/usa_small.png":
            self._send_overlay_asset(
                "artwork/usa_small.png",
                "image/png"
            )
            return

        if path == "/overlay/artwork/usa_big.png":
            self._send_overlay_asset(
                "artwork/usa_big.png",
                "image/png"
            )
            return

        if path == "/overlay/fonts/Oxanium-SemiBold.ttf":
            self._send_overlay_asset(
                "fonts/Oxanium-SemiBold.ttf",
                "font/ttf"
            )
            return

        if path == "/config":
            self.server.load_live_data()

            self._send_json(
                self.server.get_overlay_config()
            )
            return

        if path == "/data":
            self.server.load_live_data()

            self._send_json(
                self.server.overlay_data
            )
            return

        if path == "/state":
            self.server.load_live_data()

            self._send_json(
                {"in_game": self.server.in_game}
            )
            return

        if path == "/toggle-test-state":
            if not ENABLE_TEST_MODE:
                self._send_response(
                    404,
                    "text/plain; charset=utf-8",
                    "Not found"
                )
                return

            self.server.toggle_test_state()
            self._send_json(
                {"in_game": self.server.in_game}
            )
            return

        self._send_response(
            404,
            "text/plain; charset=utf-8",
            "Not found"
        ) 


class OverlayServer:
    """Local HTTP server for the Strata Browser Source overlay."""

    def __init__(self, config, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.config = config
        self.http_server = None
        self.thread = None
        self.heartbeat_thread = None
        self.heartbeat_stop_event = threading.Event()

        self.overlay_config = copy.deepcopy(
            config["overlay"]
        )
        self.overlay_data = TEST_DATA
        self.in_game = False

        self.test_position_index = 0
        self.test_data_index = 0

    def _write_heartbeat(self):
        try:
            READY_FILE.write_text(
                f"PID={os.getpid()}\n"
                f"TIMESTAMP={datetime.now().timestamp()}\n",
                encoding="utf-8"
            )
        except OSError:
            pass


    def _heartbeat_loop(self):
        self._write_heartbeat()

        while not self.heartbeat_stop_event.wait(
            HEARTBEAT_INTERVAL
        ):
            self._write_heartbeat()

    def _remove_ready_file(self):
        try:
            READY_FILE.unlink(missing_ok=True)
        except OSError:
            pass

    def start(self):
        if self.http_server is not None:
            return

        try:
            self.http_server = ThreadingHTTPServer(
                (self.host, self.port),
                _OverlayRequestHandler
            )
        except OSError as error:
            raise RuntimeError(
                f"Could not start the overlay server on "
                f"http://{self.host}:{self.port}: {error}"
            ) from error

        self.http_server.overlay_config = self.overlay_config
        self.http_server.overlay_data = self.overlay_data
        self.http_server.in_game = self.in_game
        self.http_server.toggle_test_state = self.toggle_test_state
        self.http_server.get_overlay_config = self.get_overlay_config
        self.http_server.load_live_data = self.load_live_data
        self.http_server.update_overlay_config = (
            self.update_overlay_config
        )

        self.thread = threading.Thread(
            target=self.http_server.serve_forever,
            name="StrataOverlayServer",
            daemon=True
        )
        self.thread.start()

        self.heartbeat_stop_event.clear()

        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name="StrataOverlayHeartbeat",
            daemon=True
        )

        self.heartbeat_thread.start()

        return f"http://{self.host}:{self.port}/overlay"

    def load_live_data(self):
        if ENABLE_TEST_MODE:
            return
        
        data_path = (
            get_output_directory()
            / "data.json"
        )

        try:
            with open(
                data_path,
                "r",
                encoding="utf-8"
            ) as file:

                self.overlay_data = json.load(file)

        except (
            OSError,
            json.JSONDecodeError
        ):
            return

        self.in_game = (
            "local_player_faction"
            in self.overlay_data
        )

        if self.http_server is not None:
            self.http_server.overlay_data = (
                self.overlay_data
            )

            self.http_server.in_game = (
                self.in_game
            )

    def stop(self):
        if self.http_server is None:
            return

        self.heartbeat_stop_event.set()

        if (
            self.heartbeat_thread is not None
            and self.heartbeat_thread.is_alive()
        ):
            self.heartbeat_thread.join()

        self.http_server.shutdown()
        self.http_server.server_close()

        if self.thread is not None and self.thread.is_alive():
            self.thread.join()

        self._remove_ready_file()

        self.heartbeat_thread = None
        self.thread = None
        self.http_server = None

    def set_in_game(self, in_game):
        self.in_game = bool(in_game)
        if self.http_server is not None: self.http_server.in_game = self.in_game

    def toggle_test_state(self):
        if not ENABLE_TEST_MODE:
            return

        self.test_position_index = 0
        self.set_in_game(not self.in_game)


    def cycle_test_data(self):
        if not ENABLE_TEST_MODE:
            return

        self.test_data_index = (
            self.test_data_index + 1
        ) % len(TEST_DATA_STATES)

        self.overlay_data = {
            **TEST_DATA_STATES[
                self.test_data_index
            ],
            "match_update_trigger":
                datetime.now().isoformat()
        }

        if self.http_server is not None:
            self.http_server.overlay_data = (
                self.overlay_data
            )


    def cycle_test_positions(self):
        if not ENABLE_TEST_MODE:
            return

        if self.in_game:
            combinations = TEST_POSITION_COMBINATIONS
        else:
            combinations = TEST_MENU_POSITION_COMBINATIONS

        self.test_position_index = (
            self.test_position_index + 1
        ) % len(combinations)


    def validate_overlay_config(self, overlay_config):
        """
        Validate the complete overlay configuration.

        Returns the validated configuration or raises ValueError.
        """

        if not isinstance(overlay_config, dict):
            raise ValueError(
                "Overlay configuration must be an object."
            )

        for hud_name in ("hud_1", "hud_2"):

            if hud_name not in overlay_config:
                raise ValueError(
                    f"Missing configuration for {hud_name}."
                )

            hud_config = overlay_config[hud_name]

            if not isinstance(hud_config, dict):
                raise ValueError(
                    f"{hud_name} configuration must be an object."
                )

            visibility_mode = hud_config.get("visibility_mode")
            if visibility_mode not in VISIBILITY_MODES:
                raise ValueError(
                    f"Invalid visibility mode for {hud_name}."
                )

            if not isinstance(
                hud_config.get("hide_when_observing"),
                bool
            ):
                raise ValueError(
                    f"hide_when_observing for {hud_name} "
                    f"must be true or false."
                )

            template = hud_config.get("template")
            if template not in TEMPLATES:
                raise ValueError(
                    f"Invalid template for {hud_name}."
                )

            ladder = hud_config.get("ladder")
            if ladder not in LADDERS:
                raise ValueError(
                    f"Invalid ladder for {hud_name}."
                )

            artwork_size = hud_config.get("artwork_size")
            if artwork_size not in ARTWORK_SIZES:
                raise ValueError(
                    f"Invalid artwork size for {hud_name}."
                )

            artwork_color = hud_config.get("artwork_color")
            if artwork_color not in ARTWORK_COLORS:
                raise ValueError(
                    f"Invalid artwork color for {hud_name}."
                )

            position_mode = hud_config.get("position_mode")
            if position_mode not in POSITION_MODES:
                raise ValueError(
                    f"Invalid position mode for {hud_name}."
                )

            in_game_position = hud_config.get(
                "in_game_position"
            )
            if in_game_position not in IN_GAME_POSITIONS:
                raise ValueError(
                    f"Invalid in-game position for {hud_name}."
                )

            in_menu_position = hud_config.get(
                "in_menu_position"
            )
            if in_menu_position not in IN_MENU_POSITIONS:
                raise ValueError(
                    f"Invalid in-menu position for {hud_name}."
                )

        return copy.deepcopy(overlay_config)

    def update_overlay_config(self, overlay_config):
        """
        Validate, save, and immediately apply a new overlay configuration.

        The existing configuration remains active if validation or saving fails.
        """

        validated_config = self.validate_overlay_config(
            overlay_config
        )

        save_overlay_config(
            self.config,
            validated_config
        )

        self.overlay_config = validated_config

    def get_overlay_config(self):
        config = copy.deepcopy(self.overlay_config)

        if ENABLE_TEST_MODE:
            if self.in_game:
                hud_1_position, hud_2_position = (
                    TEST_POSITION_COMBINATIONS[
                        self.test_position_index
                    ]
                )

                config["hud_1"]["in_game_position"] = hud_1_position
                config["hud_2"]["in_game_position"] = hud_2_position

            else:
                hud_1_position, hud_2_position = (
                    TEST_MENU_POSITION_COMBINATIONS[
                        self.test_position_index
                    ]
                )

                config["hud_1"]["in_menu_position"] = hud_1_position
                config["hud_2"]["in_menu_position"] = hud_2_position

        return config
