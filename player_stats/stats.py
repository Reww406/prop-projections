r"""
  Caclulate projections based on player stats..
"""
import statistics
from player_stats import scraper
import numpy as np
import re

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
WORST_RB_D = scraper.get_top_n_def_for_pos(QB_D_STATS, 5, True)
TOP_WR_D = scraper.get_top_n_def_for_pos(WR_D_STATS, 5, False)
WORST_WR_D = scraper.get_top_n_def_for_pos(WR_D_STATS, 5, True)
TOP_TE_D = scraper.get_top_n_def_for_pos(TE_D_STATS, 5, False)
WORST_TE_D = scraper.get_top_n_def_for_pos(TE_D_STATS, 5, True)

SCORE_REGEX = re.compile(r"^[WLT]{1}(\d+)[\-]{1}(\d+).*?$")

LAST_Y_STAT_W = 85
THIS_YEAR_STAT_W = 100
BLOW_OUT_STAT_W = 75

# Spread has big impact
RUSH_D_ATTEMPT_WEIGHT = 10
PASS_D_ATTEMPT_WEIGHT = 5
REC_D_ATTEMPT_WEIGHT = 10

QB_D_YDS_WEIGHT = 16
RB_D_YDS_WEIGHT = 15
WR_D_YDS_WEIGHT = 8
TE_D_YDS_WEIGHT = 8

HIGH_SPREAD = 6.5
HIGH_TOTAL = 49
LOW_TOTAL = 42

TOP_PERC = 95
BOTTOM_PERC = 5

YEARS = [scraper.CURRENT_YEAR, scraper.LAST_YEAR]

SEASON_KEY = {'2022': "2022 Regular Season", '2021': "2021 Regular Season"}
RUSHING_KEY = "Rushing"
RECEIVING_KEY = "Receiving"
FUMBLES_KEY = "Fumbles"
PASSING_KEY = "Passing"
'''
  Ideas for making projections better
  - better way to calculate mean?
  - the weather
  - Teams pace
  - Take yds when winning by a lot compare to spread to get better weight
  - Zone vs Man (man subtract from top recievers and add to bottom recievers)
  - weights based on score
'''


def remove_outliers(stat_key, stat_section):
    r"""
      Removes values X signma away from the mean.
      year: [stats]
    """
    values = []
    for year in stat_section:
        for gamelog in stat_section[year]:
            values.append(float(gamelog[stat_key]))
    values = np.array(values)
    values.sort()
    if len(values) <= 1:
        return stat_section
    mean = np.mean(values)
    std = np.std(values)
    # skew_adj = stats.skew(values) * 0.15
    new_stat_sec = {}
    for year in stat_section:
        if stat_section.get(year) is None:
            print("No: " + str(year))
            continue
        year_stats = stat_section[year]
        new_year_stats = []
        for game_log in year_stats:
            stat = float(game_log.get(stat_key))
            z = (stat - mean) / std
            if z < -1.6 or z > 1.6:
                print("Removing outlier: " + str(stat))
            else:
                new_year_stats.append(game_log)
        new_stat_sec[year] = new_year_stats
    return new_stat_sec


def get_weighted_mean(stat_key, year_for_gl):
    """
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
    return proj * (float(weight) / 100)


def get_weight_for_spread(spread, weight, proj):
    """
    weight = [high pos spread, hight neg spread, normal spread]
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

    weight_num = per_of_proj(weight[2], proj)
    if weight_num != 0.0:
        print(f"Adding {weight_num} for high close spread")
    return weight_num


def get_weight_for_def(proj, opp, top_5_d, worst_5_d, pos_weight):
    """
        Get weight for top 5 or worst 5 defense based on projection
    """
    if opp in top_5_d:
        weight = -per_of_proj(pos_weight, proj)
        print(f"Subtracting {weight} for defense")
        return weight
    if opp in worst_5_d:
        weight = per_of_proj(pos_weight, proj)
        print(f"Adding {weight} for defense")
        return weight
    return 0


def calc_rush_att_proj(gamelogs, opp, team, spread, total):
    r"""
      Calculate rush attempt projection
    """
    rush_stats = get_stats(gamelogs, RUSHING_KEY)
    proj = get_weighted_mean('ATT', remove_outliers('ATT', rush_stats))
    def_weight = get_weight_for_def(proj, opp, TOP_RB_D, WORST_RB_D,
                                    RUSH_D_ATTEMPT_WEIGHT)
    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [18, -18, 0], proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [18, -18, 0], proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [-18, 18, 0], proj)
    proj += spread_weight
    proj += def_weight
    return format_proj(proj)


def calc_pass_yds_proj(gamelogs, opp, team, spread, total):
    """
      Calc pass yds
    """
    pass_stats = get_stats(gamelogs, PASSING_KEY)
    proj = get_weighted_mean('YDS', remove_outliers('YDS', pass_stats))
    def_weight = get_weight_for_def(proj, opp, TOP_QB_D, WORST_QB_D,
                                    QB_D_YDS_WEIGHT)

    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [15, 25, 15], proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [5, 18, -15], proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [5, 15, 0], proj)

    proj += spread_weight
    proj += def_weight
    return format_proj(proj)


def calc_rush_yds_proj(gamelogs, opp, team, spread, total):
    """
      calc rush yards
    """
    rush_stats = get_stats(gamelogs, RUSHING_KEY)
    proj = get_weighted_mean('YDS', remove_outliers('YDS', rush_stats))
    def_weight = get_weight_for_def(proj, opp, TOP_RB_D, WORST_RB_D,
                                    RB_D_YDS_WEIGHT)

    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [15, -15, 10], proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [10, -12, 0], proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [12, -12, 0], proj)

    proj += spread_weight
    proj += def_weight
    return format_proj(proj)


def calc_rec_yds_proj(gamelogs, opp, team, spread, total):
    """
      Calc rec yards
    """
    rec_stats = get_stats(gamelogs, RECEIVING_KEY)
    proj = get_weighted_mean('YDS', remove_outliers('YDS', rec_stats))
    def_weight = get_weight_for_def(proj, opp, TOP_WR_D, WORST_WR_D,
                                    WR_D_YDS_WEIGHT)

    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [10, 15, 10], proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [3, 8, -3], proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [5, 8, 0], proj)

    proj += def_weight
    proj += spread_weight
    return format_proj(proj)


def calc_pass_att_proj(gamelogs, opp, team, spread, total):
    r"""
      Calculate pass attempt projection
    """
    pass_stats = get_stats(gamelogs, PASSING_KEY)
    proj = get_weighted_mean('ATT', remove_outliers('ATT', pass_stats))
    def_weight = get_weight_for_def(proj, opp, TOP_QB_D, WORST_QB_D,
                                    PASS_D_ATTEMPT_WEIGHT)

    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [-7, 13, 10], proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [0, 5, -3], proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [-5, 5, 0], proj)

    proj += spread_weight
    proj += def_weight
    return format_proj(proj)


def calc_pass_comp_proj(gamelogs, opp, team, spread, total):
    r"""
      Calculate pass completion projection
    """
    pass_stats = get_stats(gamelogs, PASSING_KEY)
    proj = get_weighted_mean('CMP', remove_outliers('CMP', pass_stats))
    def_weight = get_weight_for_def(proj, opp, TOP_QB_D, WORST_QB_D,
                                    PASS_D_ATTEMPT_WEIGHT)

    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [-7, 10, 10], proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [0, 5, -3], proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [-5, 5, 0], proj)

    proj += spread_weight
    proj += def_weight
    return format_proj(proj)


def calc_rec_proj(gamelogs, opp, team, spread, total):
    r"""
      Calculate receptions projection
    """
    rec_stats = get_stats(gamelogs, RECEIVING_KEY)
    proj = get_weighted_mean('REC', remove_outliers('REC', rec_stats))
    def_weight = get_weight_for_def(proj, opp, TOP_WR_D, WORST_WR_D,
                                    REC_D_ATTEMPT_WEIGHT)

    spread_weight = 0
    team_spread = float(spread.get(team))
    if total >= HIGH_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [8, 10, 5], proj)
    elif total <= LOW_TOTAL:
        spread_weight = get_weight_for_spread(team_spread, [0, 8, 0], proj)
    else:
        spread_weight = get_weight_for_spread(team_spread, [4, 10, 0], proj)

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
            print("No game logs for: " + year)
        else:
            for game in gamelogs[year]:
                stat_section = game[stat_key]
                stat_section["Result"] = game[SEASON_KEY[year]]["Result"]
                stat_section["OPP"] = game[SEASON_KEY[year]]['OPP']
                player_stats.append(stat_section)
            year_stats[year] = player_stats
    return year_stats
