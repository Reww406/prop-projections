"""
    Holds Constants used across the script
"""

SEASON_2022 = '2022 Regular Season'
SEASON_2021 = '2021 Regular Season'
SEASON_2020 = '2020 Regular Season'
SEASON_2019 = '2019 Regular Season'

LAST_YEAR = '2021'
CURRENT_YEAR = '2022'

RUSHING_KEY = "Rushing"
RECEIVING_KEY = "Receiving"
FUMBLES_KEY = "Fumbles"
PASSING_KEY = "Passing"

SECTION_FOR_TABLE = {
    PASSING_KEY: "player_pass_gl",
    RECEIVING_KEY: "player_rec_gl",
    RUSHING_KEY: "player_rush_gl"
}

TOP_QB_D_REC_YDS_WEIGHT = -0.75
WORST_QB_D_REC_YDS_WEIGHT = 5.75

TOP_RB_D_YDS_WEIGHT = -2.75
WORST_RB_D_YDS_WEIGHT = 0

# -39.5
TOP_WR_D_YDS_WEIGHT = -4.25
WORST_WR_D_YDS_WEIGHT = 5.75

LINE_HURT_WEIGHT_RUSH = 11.5
LINE_HURT_WEIGHT_REC = -2.0
STARTING_WR_HURT_WEIGHT = 2.0
