r"""
  Caclulate projections based on player stats..
"""

import re
import statistics
import numpy as np
from player_stats import scraper

QB_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("qb"))
RB_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("rb"))
WR_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("wr"))
TE_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("te"))

TOP_QB_D = scraper.get_top_n_def_for_pos(QB_D_STATS, 5, False)
WORST_QB_D = scraper.get_top_n_def_for_pos(QB_D_STATS, 5, True)
TOP_RB_D = scraper.get_top_n_def_for_pos(RB_D_STATS, 5, False)
WORST_RB_D = scraper.get_top_n_def_for_pos(RB_D_STATS, 5, True)
TOP_WR_D = scraper.get_top_n_def_for_pos(WR_D_STATS, 5, False)
WORST_WR_D = scraper.get_top_n_def_for_pos(WR_D_STATS, 5, True)
TOP_TE_D = scraper.get_top_n_def_for_pos(TE_D_STATS, 5, False)
WORST_TE_D = scraper.get_top_n_def_for_pos(TE_D_STATS, 5, True)

SCORE_REGEX = re.compile(r"^[WLT]{1}(\d+)[\-]{1}(\d+).*?$")

LAST_Y_STAT_W = 85
THIS_YEAR_STAT_W = 100
BLOW_OUT_STAT_W = 70

# Spread has big impact
TOP_RUSH_D_ATT_WEIGHT = -15
TOP_PASS_D_ATT_WEIGHT = -5
TOP_REC_D_REC_WEIGHT = -12

WORST_RUSH_D_ATT_WEIGHT = 18
WORST_PASS_D_ATT_WEIGHT = 10
WORST_REC_D_REC_WEIGHT = 15

# TODO do good and bad
TOP_QB_D_YDS_WEIGHT = -10
TOP_RB_D_YDS_WEIGHT = -15
TOP_WR_D_YDS_WEIGHT = -5
TOP_TE_D_YDS_WEIGHT = -8

WORST_QB_D_YDS_WEIGHT = 20
WORST_RB_D_YDS_WEIGHT = 20
WORST_WR_D_YDS_WEIGHT = 14
WORST_TE_D_YDS_WEIGHT = 14

CLOSE_NEG = -3
CLOSE_POS = 3
HIGH_SPREAD = 8
HIGH_TOTAL = 49
LOW_TOTAL = 40

YEARS = [scraper.CURRENT_YEAR, scraper.LAST_YEAR]

SEASON_KEY = {'2022': "2022 Regular Season", '2021': "2021 Regular Season"}
RUSHING_KEY = "Rushing"
RECEIVING_KEY = "Receiving"
FUMBLES_KEY = "Fumbles"
PASSING_KEY = "Passing"
'''
    Ideas for making projections better
    - better way to calculate mean?
    - Teams pace
    - Take yds when winning by a lot compare to spread to get better weight
    - weights based on score
    - throw away QB rush...
    - Do good vs bad weight..
    - Take into account pass for run ratio top 3 bottom 3 adjust averges..
    - in weighted averge boost most recent games

    Ideas from stats books
    - Use percentiles or MAD which is a more robust approximation
        Robust meaning less sensitive to outliers
    - Calculate correlation between score and yds +- to see if we should
        actually be boosting or not.


'''


# TODO I dont think this would be problem with a perctile type outlier
def remove_non_starts(stat_key, sec_key, stat_section):
    """
        :param stat_key which stat is being grabbed
        :param sec_key only cares if passing
        :param stat_section either rushing passing or recieving
        Remove non start games for QB specifically
    """
    values = []
    if sec_key == PASSING_KEY:
        for year in stat_section:
            for gamelog in stat_section[year]:
                stat = float(gamelog[stat_key])
                if stat > 0.0:
                    values.append(stat)
                else:
                    print("Removing passing non stater game stats")
    else:
        for year in stat_section:
            for gamelog in stat_section[year]:
                values.append(float(gamelog[stat_key]))

    return values


# Use percentiles or MAD which is a more robust approximatin
# TODO try IQR on with more stats..
def remove_outliers(stat_key, sec_key, gamelogs):
    r"""
        :param stat_key = YDS, ATT, CMP, REC
        :param sec_key = Passing, Rushing or Recieving
        :param gamelogs = the players game logs
        Removes values X signma away from the mean.
        year: [stats]
    """
    stat_section = get_stats(gamelogs, sec_key)
    values = remove_non_starts(stat_key, sec_key, stat_section)
    values = np.array(values)
    values.sort()
    if len(values) <= 1:
        # Can't get mean if it's one stat...
        return stat_section
    mean = np.mean(values)
    std = np.std(values)
    new_stat_sec = {}
    for year, year_stats in stat_section.items():
        if year_stats is None:
            continue
        outliers_removed = []
        for game_log in year_stats:
            stat = float(game_log.get(stat_key))
            z = (stat - mean) / std
            if z < -2.0 or z > 2.0:
                print(f"Removing outlier: {stat}")
            else:
                outliers_removed.append(game_log)
        new_stat_sec[year] = outliers_removed
    return new_stat_sec


# This can be refactored
def get_weighted_mean(stat_key, year_for_gl):
    """
        Gets weighted mean of 2021 stats 2022 stats and blow outs
        Calculate weighted averge..
    """
    last_year_yds = this_years_yds = blow_out_game_yds = []
    if year_for_gl.get('2021') is not None:
        for game_log in year_for_gl['2021']:
            score_match = SCORE_REGEX.match(game_log['Result'])
            diff = abs(int(score_match.group(1)) - int(score_match.group(2)))
            if diff > 20:
                blow_out_game_yds.append(float(game_log[stat_key]))
            else:
                last_year_yds.append(float(game_log[stat_key]))
    if year_for_gl.get('2022') is not None:
        for game_log in year_for_gl['2022']:
            score_match = SCORE_REGEX.match(game_log['Result'])
            diff = abs(int(score_match.group(1)) - int(score_match.group(2)))
            if diff > 20:
                blow_out_game_yds.append(float(game_log[stat_key]))
            else:
                this_years_yds.append(float(game_log[stat_key]))

    weighted_this_year = 100 * statistics.mean(this_years_yds)
    weighted_blow_out = 70 * statistics.mean(blow_out_game_yds)
    weighted_last_year = 85 * statistics.mean(last_year_yds)

    return (weighted_blow_out + weighted_last_year +
            weighted_this_year) / (100 + 70 + 85)


def format_proj(projection) -> str():
    r"""
      Create project string for file
    """
    return "{:.1f}".format(projection)


PROPS_TO_PARSE = [
    "Pass Yds", "Pass Completions", "Pass Attempts", "Rush Yds", "Rec Yds",
    "Receptions", "Rush Attempts"
]


def per_of_proj(weight, proj):
    """
        Get percentage of proj based on weight
    """
    flt_weight = float(weight) / 100
    print(f"Proj {proj} weight: {flt_weight}")
    return proj * (float(weight) / 100)


def get_weight_for_spread(spread, weight, proj):
    """
    Calculates what the weight should be based on spread
    :param weight = [very underdog, very fav, slight underdog, slight fav, close game]
  """
    if spread >= HIGH_SPREAD:
        weight_num = per_of_proj(weight[0], proj)
        if weight_num != 0.0:
            print(f"Adding {weight_num} for high pos spread")
        return weight_num

    if spread <= -HIGH_SPREAD:
        weight_num = per_of_proj(weight[1], proj)
        if weight_num != 0.0:
            print(f"Adding {weight_num} for high neg spread")
        return weight_num

    if spread >= CLOSE_POS:
        weight_num = per_of_proj(weight[2], proj)
        if weight_num != 0.0:
            print(f"Adding {weight_num} for middle pos spread")
        return weight_num

    if spread <= CLOSE_NEG:
        weight_num = per_of_proj(weight[3], proj)
        if weight_num != 0.0:
            print(f"Adding {weight_num} for middle neg spread")
        return weight_num

    weight_num = per_of_proj(weight[4], proj)
    if weight_num != 0.0:
        print(f"Adding {weight_num} for close spread")
    return weight_num


def get_weight_for_def(proj, opp, top_5_d, worst_5_d, worst_pos_weight,
                       top_pos_weight):
    """
        Get weight for top 5 or worst 5 defense based on projection
    """
    if opp in top_5_d:
        weight = per_of_proj(top_pos_weight, proj)
        print(f"Subtracting {weight} for defense")
        return weight
    if opp in worst_5_d:
        weight = per_of_proj(worst_pos_weight, proj)
        print(f"Adding {weight} for defense")
        return weight
    return 0


def calc_rush_att_proj(gamelogs, opp, team, spread, total):
    r"""
      Calculate rush attempt projection
    """
    proj = get_weighted_mean('ATT',
                             remove_outliers('ATT', RUSHING_KEY, gamelogs))
    def_weight = get_weight_for_def(proj, opp, TOP_RB_D, WORST_RB_D,
                                    WORST_RUSH_D_ATT_WEIGHT,
                                    TOP_RUSH_D_ATT_WEIGHT)
    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [-8, 14, -4, 7, 0],
                                              proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [-6, 8, -6, 6, 0],
                                              proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [-6, 6, 2, 6, 0],
                                              proj)
    proj += spread_weight
    proj += def_weight
    return format_proj(proj)


def calc_pass_yds_proj(gamelogs, opp, team, spread, total):
    """
      Calc pass yds
    """
    proj = get_weighted_mean('YDS',
                             remove_outliers('YDS', PASSING_KEY, gamelogs))
    def_weight = get_weight_for_def(proj, opp, TOP_QB_D, WORST_QB_D,
                                    WORST_QB_D_YDS_WEIGHT, TOP_QB_D_YDS_WEIGHT)

    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread,
                                              [20, 25, 18, 20, 15], proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [12, 8, 5, -10, -5],
                                              proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [13, 10, 8, -5, -8],
                                              proj)

    proj += spread_weight
    proj += def_weight
    return format_proj(proj)


def calc_rush_yds_proj(gamelogs, opp, team, spread, total):
    """
      calc rush yards
    """
    proj = get_weighted_mean('YDS',
                             remove_outliers('YDS', RUSHING_KEY, gamelogs))
    def_weight = get_weight_for_def(proj, opp, TOP_RB_D, WORST_RB_D,
                                    WORST_RB_D_YDS_WEIGHT, TOP_RB_D_YDS_WEIGHT)

    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread,
                                              [-11, 12, -7, 7, 10], proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [-10, 4, 4, 10, 0],
                                              proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [4, 8, 4, 6, 4],
                                              proj)

    proj += spread_weight
    proj += def_weight
    return format_proj(proj)


def calc_rec_yds_proj(gamelogs, opp, team, spread, total):
    """
      Calc rec yards
    """
    proj = get_weighted_mean('YDS',
                             remove_outliers('YDS', RECEIVING_KEY, gamelogs))
    def_weight = get_weight_for_def(proj, opp, TOP_WR_D, WORST_WR_D,
                                    WORST_WR_D_YDS_WEIGHT, TOP_WR_D_YDS_WEIGHT)

    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [10, 12, 6, 5, 10],
                                              proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [8, 10, 8, 4, 0],
                                              proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [14, 12, 14, 2, 4],
                                              proj)

    proj += def_weight
    proj += spread_weight
    return format_proj(proj)


def calc_pass_att_proj(gamelogs, opp, team, spread, total):
    r"""
      Calculate pass attempt projection
    """
    proj = get_weighted_mean('ATT',
                             remove_outliers('ATT', PASSING_KEY, gamelogs))
    def_weight = get_weight_for_def(proj, opp, TOP_QB_D, WORST_QB_D,
                                    WORST_PASS_D_ATT_WEIGHT,
                                    TOP_PASS_D_ATT_WEIGHT)

    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [12, 8, 10, 8, 10],
                                              proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [8, 5, 4, 3, -6],
                                              proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [10, 2, 5, 2, -6],
                                              proj)

    proj += spread_weight
    proj += def_weight
    return format_proj(proj)


def calc_pass_comp_proj(gamelogs, opp, team, spread, total):
    r"""
      Calculate pass completion projection
    """
    proj = get_weighted_mean('CMP',
                             remove_outliers('CMP', PASSING_KEY, gamelogs))
    def_weight = get_weight_for_def(proj, opp, TOP_QB_D, WORST_QB_D,
                                    WORST_PASS_D_ATT_WEIGHT,
                                    TOP_PASS_D_ATT_WEIGHT)

    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [8, 3, 5, 3, 10],
                                              proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [5, 0, 5, 3, -6],
                                              proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [5, 3, 5, 3, -6],
                                              proj)

    proj += spread_weight
    proj += def_weight
    return format_proj(proj)


def calc_rec_proj(gamelogs, opp, team, spread, total):
    r"""
      Calculate receptions projection
    """
    proj = get_weighted_mean('REC',
                             remove_outliers('REC', RECEIVING_KEY, gamelogs))
    def_weight = get_weight_for_def(proj, opp, TOP_WR_D, WORST_WR_D,
                                    WORST_REC_D_REC_WEIGHT,
                                    TOP_REC_D_REC_WEIGHT)

    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [12, 10, 7, 5, 8],
                                              proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [4, 8, 4, 4, 0],
                                              proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [10, 6, 10, 4, 4],
                                              proj)

    proj += spread_weight
    proj += def_weight
    return format_proj(proj)


def get_stats(gamelogs, stat_key):
    r"""
      Get list dictionary of stats from gamelog
    """
    year_stats = {}
    for year in YEARS:
        player_stats = []
        if gamelogs.get(year) is None:
            print(f"No game logs for: {year}")
        else:
            for game in gamelogs[year]:
                stat_section = game[stat_key]
                stat_section["Result"] = game[SEASON_KEY[year]]["Result"]
                stat_section["OPP"] = game[SEASON_KEY[year]]['OPP']
                player_stats.append(stat_section)
            year_stats[year] = player_stats
    return year_stats


def get_win_loss_margin(gamelog):
    pass


# Mixon, Sinlgetary, Montgomery,
def calc_rb_corr():
    """
        score to yards
        score to attempts
    """
    team_player = {
        'CIN': 'J. Mixon',
        'BUF': 'D. Singletary',
        'CHI': 'D. Montgomery',
        'TEN': 'D. Henry',
        'TB': 'L. Fournette'
    }

    gamelogs = [
        scraper.get_player_gamelogs(team, player)
        for team, player in team_player
    ]

    for log in gamelogs:
        print(f"{log} \n\n")


calc_rb_corr()