"""
Continuous test utility for the Strata Streamer Tool.

Simulates the current game-start / game-end lifecycle while also running
the local OverlayServer, so the browser/OBS overlay can be tested against
the same HTTP endpoints used by the real application.

Each cycle:
1. Start with the current Elo/rank.
2. Randomly select GLA, USA, or China.
3. Write the current rating/rank state.
4. Call write_game_start() to add local_player_faction.
5. Wait 3 seconds.
6. Generate a random Elo/rank change and calculate the new values.
7. Write the updated rating/rank state, including mirrored monthly changes.
8. Call write_game_end() to remove local_player_faction.
9. Wait 10 seconds and repeat.

Stop with Ctrl+C.
"""

import random
import time

from writer import OutputWriter
from overlay_server import OverlayServer
from app_paths import get_output_directory


FACTIONS = {
    "GLA": 4,
    "USA": 2,
    "China": 8,
}

PLAYER_ID = 12345
STARTING_RATING = 1500
STARTING_RANK = 100
STARTING_MATCHES = 100


def generate_changes():
    """Generate an Elo change from +/-2..40 and a rank change from 0..15.

    When rank_change is non-zero, its sign always matches the Elo change.
    """
    elo_change = random.randint(2, 40)

    if random.choice((True, False)):
        elo_change = -elo_change

    rank_change = random.randint(0, 15)

    if rank_change and elo_change < 0:
        rank_change = -rank_change

    return elo_change, rank_change


def build_changes(
    elo_change,
    rank_change,
    session_elo_change,
    session_rank_change,
):
    """Build the changes structure expected by the current writer.

    Monthly changes intentionally mirror the overall changes for this
    simulator, since there is only one simulated rating/rank progression.
    """
    return {
        "overall_rating_change": elo_change,
        "overall_rank_change": rank_change,
        "monthly_rating_change": elo_change,
        "monthly_rank_change": rank_change,
        "overall_session_rating_change": session_elo_change,
        "overall_session_rank_change": session_rank_change,
        "monthly_session_rating_change": session_elo_change,
        "monthly_session_rank_change": session_rank_change,
    }


def write_state(
    writer,
    rating,
    rank,
    matches,
    changes,
    trigger_match_overlays=False,
):
    """Write a rating state using the current OutputWriter interface.

    The current writer expects the monthly data under the input key
    'season', then writes it to data.json as 'monthly'.
    """
    data = {
        "overall": {
            "rating": rating,
            "matches": matches,
            "rank": rank,
            "peak_rating": rating,
        },
        "season": {
            "rating": rating,
            "matches": matches,
            "rank": rank,
            "peak_rating": rating,
        },
    }

    writer.write_output_files(
        data=data,
        player_id=PLAYER_ID,
        changes=changes,
        update_match_changes=trigger_match_overlays,
        trigger_match_overlays=trigger_match_overlays,
    )


def main():
    output_directory = get_output_directory()
    writer = OutputWriter(output_directory)

    # Run the same local HTTP server used by the actual overlay. This allows
    # OBS/browser-source testing against http://127.0.0.1:<port>/overlay.
    overlay_server = OverlayServer()
    overlay_url = overlay_server.start()

    rating = STARTING_RATING
    rank = STARTING_RANK
    matches = STARTING_MATCHES

    session_elo_change = 0
    session_rank_change = 0

    print("Strata Streamer Tool match simulator")
    print(f"Output directory: {output_directory}")
    print(f"Overlay server: {overlay_url}")
    print(f"Starting Elo: {rating}")
    print(f"Starting rank: {rank}")
    print("Press Ctrl+C to stop.")
    print()

    try:
        while True:
            faction = random.choice(tuple(FACTIONS))

            # ----------------------------------------------------------
            # GAME START
            # ----------------------------------------------------------
            # Write the current rating/rank first. write_game_start()
            # then adds local_player_faction to data.json.
            start_changes = build_changes(
                0,
                0,
                session_elo_change,
                session_rank_change,
            )

            write_state(
                writer=writer,
                rating=rating,
                rank=rank,
                matches=matches,
                changes=start_changes,
                trigger_match_overlays=False,
            )

            writer.write_game_start(FACTIONS[faction])

            # The OverlayServer reads data.json on each /data or /state
            # request, so the newly added faction will be picked up by the
            # next browser-source poll.
            print(
                f"In-game: Elo {rating} (+0), Rank #{rank} (+0), "
                f"Faction {faction}"
            )

            # Generate the result now, but don't write it until after the
            # simulated 3-second game duration.
            elo_change, rank_change = generate_changes()

            new_rating = rating + elo_change
            new_rank = max(1, rank - rank_change)

            session_elo_change += elo_change
            session_rank_change += rank_change
            new_matches = matches + 1

            time.sleep(3)

            # ----------------------------------------------------------
            # GAME END
            # ----------------------------------------------------------

            # Remove local_player_faction after the result has been written.
            # This makes the OverlayServer's /state endpoint transition back
            # to menu state on its next request.
            writer.write_game_end()
            
            end_changes = build_changes(
                elo_change,
                rank_change,
                session_elo_change,
                session_rank_change,
            )

            write_state(
                writer=writer,
                rating=new_rating,
                rank=new_rank,
                matches=new_matches,
                changes=end_changes,
                trigger_match_overlays=True,
            )



            print(
                f"Game ended: Elo {new_rating} ({elo_change:+d}), "
                f"Rank #{new_rank} ({rank_change:+d})"
            )
            print("Waiting 10 seconds for the next simulated match...")
            print()

            rating = new_rating
            rank = new_rank
            matches = new_matches

            time.sleep(10)

    except KeyboardInterrupt:
        print()
        print("Simulation stopped.")

    finally:
        overlay_server.stop()


if __name__ == "__main__":
    main()
