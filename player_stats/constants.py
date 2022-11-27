CURR_SEASON = '2022 Regular Season'
LAST_SEASON = '2021 Regular Season'

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

# [very underdog, very fav, slight underdog, slight fav, close game]
RUSH_YDS_AT_S_W = [10.25, -2.0, 27.5, -12.25, -11.0]

REC_YDS_HT_S_W = [19.25, 0, -8.5, 5.75, -8.25]

REC_YDS_LT_S_W = [-1.5, 9.25, -6.75, 5.5, -20.5]

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

# error 36
LAST_Y_STAT_W = 46
# error 208
THIS_YEAR_STAT_W = 222
# 125
BLOW_OUT_STAT_W = 49