"""
Test utility for the Strata Streamer Tool output files.

Place this file next to main.py/writer.py (normally in src/) and run:

    python test_output.py

The script uses the exact same output-directory helper as main.py and
performs one simulated match/update. Run it again whenever you want
another update.
"""

import random

from writer import OutputWriter
from app_paths import get_output_directory


def generate_test_data(
    overall_rating,
    overall_rank,
    monthly_rating,
    monthly_rank,
):
    """Generate one plausible rating update."""

    overall_change = random.choice(
        [-9, -7, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 7, 9, 12, 15]
    )

    monthly_change = random.choice(
        [-5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 8, 10]
    )

    new_overall_rating = overall_rating + overall_change
    new_monthly_rating = monthly_rating + monthly_change

    if overall_change > 0:
        overall_rank_delta = random.choice([-2, -1, 0, 0, 1])
    else:
        overall_rank_delta = random.choice([0, 1, 1, 2, 3])

    if monthly_change > 0:
        monthly_rank_delta = random.choice([-2, -1, 0, 0, 1])
    else:
        monthly_rank_delta = random.choice([0, 1, 1, 2, 3])

    new_overall_rank = max(1, overall_rank + overall_rank_delta)
    new_monthly_rank = max(1, monthly_rank + monthly_rank_delta)

    return (
        new_overall_rating,
        new_overall_rank,
        new_monthly_rating,
        new_monthly_rank,
    )


def main():
    import argparse
    import time

    parser = argparse.ArgumentParser(
        description="Generate simulated Strata match output."
    )
    parser.add_argument(
        "iterations",
        nargs="?",
        type=int,
        default=1,
        help="Number of simulated matches to generate (default: 1).",
    )

    args = parser.parse_args()

    if args.iterations < 1:
        parser.error("iterations must be at least 1.")

    output_directory = get_output_directory()
    writer = OutputWriter(output_directory)

    # Start from a plausible rating/rank baseline.
    overall_rating = random.randint(1450, 1650)
    overall_rank = random.randint(10, 30)

    monthly_rating = random.randint(1450, 1650)
    monthly_rank = random.randint(10, 30)

    overall_rating_start = overall_rating
    overall_rank_start = overall_rank
    monthly_rating_start = monthly_rating
    monthly_rank_start = monthly_rank

    overall_matches = 100
    monthly_matches = 10

    print("Strata Streamer Tool output tester")
    print(f"Output directory: {output_directory}")
    print(f"Simulated matches: {args.iterations}")
    print()

    for iteration in range(1, args.iterations + 1):

        (
            new_overall_rating,
            new_overall_rank,
            new_monthly_rating,
            new_monthly_rank,
        ) = generate_test_data(
            overall_rating,
            overall_rank,
            monthly_rating,
            monthly_rank,
        )

        changes = {
            "overall_rating_change":
                new_overall_rating - overall_rating,

            "overall_rank_change":
                new_overall_rank - overall_rank,

            "monthly_rating_change":
                new_monthly_rating - monthly_rating,

            "monthly_rank_change":
                new_monthly_rank - monthly_rank,

            # Session changes are cumulative because they are measured
            # against the original baseline from before the first match.
            "overall_session_rating_change":
                new_overall_rating - overall_rating_start,

            "overall_session_rank_change":
                new_overall_rank - overall_rank_start,

            "monthly_session_rating_change":
                new_monthly_rating - monthly_rating_start,

            "monthly_session_rank_change":
                new_monthly_rank - monthly_rank_start,
        }

        data = {
            "overall": {
                "rating": new_overall_rating,
                "rank": new_overall_rank,
                "matches": overall_matches + iteration,
            },
            "monthly": {
                "rating": new_monthly_rating,
                "rank": new_monthly_rank,
                "matches": monthly_matches + iteration,
            },
        }

        writer.write_output_files(
            data=data,
            player_id=12345,
            changes=changes,
            update_match_changes=True,
            trigger_match_overlays=True,
        )

        print(
            f"Match {iteration}/{args.iterations}: "
            f"Overall Elo {new_overall_rating} "
            f"({changes['overall_rating_change']:+d}), "
            f"Rank #{new_overall_rank} | "
            f"Monthly Elo {new_monthly_rating} "
            f"({changes['monthly_rating_change']:+d}), "
            f"Rank #{new_monthly_rank}"
        )

        overall_rating = new_overall_rating
        overall_rank = new_overall_rank
        monthly_rating = new_monthly_rating
        monthly_rank = new_monthly_rank

        if iteration < args.iterations:
            print("Waiting 10 seconds for the next simulated match...")
            time.sleep(10)

    print()
    print("Test output generation completed.")


if __name__ == "__main__":
    main()
