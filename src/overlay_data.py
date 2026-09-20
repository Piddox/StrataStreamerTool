"""Temporary overlay test data."""

TEST_DATA_STATES = [
    {
        "player_id": 12345,
        "overall": {
            "rating": 1850,
            "rank": 42
        },
        "monthly": {
            "rating": 1842,
            "rank": 38
        },
        "changes": {
            "overall_rating_change": 0,
            "overall_rank_change": 0,
            "monthly_rating_change": 0,
            "monthly_rank_change": 0
        }
    },
    {
        "player_id": 12345,
        "overall": {
            "rating": 1875,
            "rank": 39
        },
        "monthly": {
            "rating": 1867,
            "rank": 36
        },
        "changes": {
            "overall_rating_change": 558,
            "overall_rank_change": 0,
            "monthly_rating_change": 225,
            "monthly_rank_change": 2,

            "overall_session_rating_change": 25,
            "overall_session_rank_change": 3,
            "monthly_session_rating_change": 18,
            "monthly_session_rank_change": 2
        }
    },
    {
        "player_id": 12345,
        "overall": {
            "rating": 1857,
            "rank": 41
        },
        "monthly": {
            "rating": 1849,
            "rank": 38
        },
        "changes": {
            "overall_rating_change": -18,
            "overall_rank_change": -1062,
            "monthly_rating_change": -18,
            "monthly_rank_change": -2,

            "overall_session_rating_change": -18,
            "overall_session_rank_change": -2,
            "monthly_session_rating_change": -12,
            "monthly_session_rank_change": -1
        }
    },
    {
        "player_id": 12345,
        "overall": {
            "rating": 1857,
            "rank": 41
        },
        "monthly": {
            "rating": 1849,
            "rank": 38
        },
        "changes": {
            "overall_rating_change": 0,
            "overall_rank_change": 0,
            "monthly_rating_change": 0,
            "monthly_rank_change": 0,

            "overall_session_rating_change": -18,
            "overall_session_rank_change": -2,
            "monthly_session_rating_change": -12,
            "monthly_session_rank_change": -1
        }
    }
]

TEST_DATA = TEST_DATA_STATES[0]