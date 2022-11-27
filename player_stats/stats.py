r"""
  Caclulate projections based on player stats..
"""

import re
import statistics
import numpy as np
from matplotlib import pyplot as plt
from player_stats import scraper, sqllite_utils
from player_stats import constants as const

QB_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("qb"))
RB_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("rb"))
WR_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("wr"))
# TE_D_STATS = scraper.get_pos_defense_ranking(
#     scraper.RANKING_FOR_POS_REGEX.get("te"))

TOP_QB_D = scraper.get_top_n_def_for_pos(QB_D_STATS, 5, False)
WORST_QB_D = scraper.get_top_n_def_for_pos(QB_D_STATS, 10, True)
TOP_RB_D = scraper.get_top_n_def_for_pos(RB_D_STATS, 5, False)
WORST_RB_D = scraper.get_top_n_def_for_pos(RB_D_STATS, 5, True)
TOP_WR_D = scraper.get_top_n_def_for_pos(WR_D_STATS, 3, False)
WORST_WR_D = scraper.get_top_n_def_for_pos(WR_D_STATS, 5, True)
# TODO Fix TE Defense..
# TOP_TE_D = scraper.get_top_n_def_for_pos(TE_D_STATS, 5, False)
# WORST_TE_D = scraper.get_top_n_def_for_pos(TE_D_STATS, 5, True)

SCORE_REGEX = re.compile(r"^[WLT]{1}(\d+)[\-]{1}(\d+).*?$")
OPP_REGEX = re.compile(r"^(@|vs)(\w+)$")

# Spread has big impact

CLOSE_NEG = -2.5
CLOSE_POS = 2.5
HIGH_SPREAD = 8
AVG_TOTAL = 46

YEARS = [const.CURRENT_YEAR, const.LAST_YEAR]

SEASON_KEY = {
    const.CURRENT_YEAR: const.CURR_SEASON,
    const.LAST_YEAR: const.LAST_SEASON
}
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
    # if sec_key == const.PASSING_KEY:
    #     for year in stat_section:
    #         for gamelog in stat_section[year]:
    #             stat = float(gamelog[stat_key])
    #             if stat > 0.0:
    #                 values.append(stat)
    #             else:
    #                 #print("Removing passing non stater game stats")
    #                 pass
    # else:
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
    stat_section = get_stats(gamelogs)
    values = remove_non_starts(stat_key, sec_key, stat_section)
    values = np.array(values)
    if len(values) <= 1:
        # Can't get mean if it's one stat...
        return stat_section
    median = np.median(values)
    deviation_from_med = values - median
    mad = np.median(np.abs(deviation_from_med))
    new_stat_sec = {}
    for year, year_stats in stat_section.items():
        if year_stats is None:
            continue
        outliers_removed = []
        for game_log in year_stats:
            stat = float(game_log.get(stat_key))
            if mad != 0.0:
                mod_zscore = 0.6745 * (stat - median) / mad
                if mod_zscore < -2.35 or mod_zscore > 2.35:
                    # print(f"Removing outlier: {stat}")
                    pass
                else:
                    outliers_removed.append(game_log)
            else:
                outliers_removed.append(game_log)
        new_stat_sec[year] = outliers_removed
    return new_stat_sec


def _calc_weighted_mean(this_year_yds, last_year_yds, blow_out):
    means = []
    weights = []
    if len(this_year_yds) > 1:
        means.append(statistics.mean(this_year_yds))
        weights.append(const.THIS_YEAR_STAT_W)
    if len(last_year_yds) > 1:
        means.append(statistics.mean(last_year_yds))
        weights.append(const.LAST_Y_STAT_W)
    if len(blow_out) > 1:
        means.append(statistics.mean(blow_out))
        weights.append(const.BLOW_OUT_STAT_W)
    if not means or not weights:
        return 0
    if len(means) == 1:
        return np.mean(means)
    return np.average(means, weights=weights)


# This can be refactored
def get_weighted_mean(stat_key, year_for_gl):
    """
        Gets weighted mean of 2021 stats 2022 stats and blow outs
        Calculate weighted averge..
    """
    last_year_yds, this_years_yds, blow_out_game_yds = [], [], []
    if year_for_gl.get('2021') is not None:
        for game_log in year_for_gl['2021']:
            score_match = SCORE_REGEX.match(game_log['result'])
            diff = abs(int(score_match.group(1)) - int(score_match.group(2)))
            if diff > 23:
                blow_out_game_yds.append(float(game_log[stat_key]))
            else:
                last_year_yds.append(float(game_log[stat_key]))
    if year_for_gl.get('2022') is not None:
        for game_log in year_for_gl['2022']:
            score_match = SCORE_REGEX.match(game_log['result'])
            diff = abs(int(score_match.group(1)) - int(score_match.group(2)))
            if diff > 23:
                blow_out_game_yds.append(float(game_log[stat_key]))
            else:
                this_years_yds.append(float(game_log[stat_key]))

    weighted_mean = _calc_weighted_mean(this_years_yds, last_year_yds,
                                        blow_out_game_yds)
    return weighted_mean


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
    # print(f"Proj {proj} weight: {flt_weight}")
    return proj * (float(weight) / 100.00)


def get_weight_for_spread(spread, weight, proj):
    """
    Calculates what the weight should be based on spread
    :param weight = [very underdog, very fav, slight underdog, slight fav, close game]
  """
    if spread >= HIGH_SPREAD:
        weight_num = per_of_proj(weight[0], proj)
        # if weight_num != 0.0:
        #     print(f"Adding {weight_num} for high pos spread")
        return weight_num

    if spread <= -HIGH_SPREAD:
        weight_num = per_of_proj(weight[1], proj)
        # if weight_num != 0.0:
        #     print(f"Adding {weight_num} for high neg spread")
        return weight_num

    if spread >= CLOSE_POS:
        weight_num = per_of_proj(weight[2], proj)
        # if weight_num != 0.0:
        #     print(f"Adding {weight_num} for middle pos spread")
        return weight_num

    if spread <= CLOSE_NEG:
        weight_num = per_of_proj(weight[3], proj)
        # if weight_num != 0.0:
        #     print(f"Adding {weight_num} for middle neg spread")
        return weight_num

    weight_num = per_of_proj(weight[4], proj)
    # if weight_num != 0.0:
    # print(f"Adding {weight_num} for close spread")
    return weight_num


def get_weight_for_def(proj, opp, top_d, worst_d, worst_pos_weight,
                       top_pos_weight):
    """
        Get weight for top 5 or worst 5 defense based on projection
    """
    if opp in top_d:
        weight = per_of_proj(top_pos_weight, proj)
        # print(f"Subtracting {weight} for defense")
        return weight
    if opp in worst_d:
        weight = per_of_proj(worst_pos_weight, proj)
        # print(f"Adding {weight} for defense")
        return weight
    return 0


def calculate_ats(player_name, team, stats_sec, stat, odd_num, db):
    """
        Returns percent time that player has hit the over
    """
    gamelogs = sqllite_utils.get_player_stats_sec(player_name, team, stats_sec,
                                                  db)
    total = 0.0
    over = 0.0
    for log in gamelogs:
        if log.get(stat) > odd_num:
            over += 1.0
        total += 1.0
    return "{:.2f}".format(float(over / total) * 100)


def _get_wr_hurt_weight(team, hurt_pos_for_team, proj):
    if hurt_pos_for_team.get(team) is not None:
        if 'WR' in hurt_pos_for_team.get(team):
            return per_of_proj(const.STARTING_WR_HURT_WEIGHT, proj)
    return 0


def _get_line_hurt_weight(team, hurt_pos_for_team, proj, one_hurt_w):
    if hurt_pos_for_team.get(team) is not None:
        for pos in hurt_pos_for_team.get(team):
            if pos in ['LT', 'LG', 'C', 'RG', 'RT']:
                return per_of_proj(one_hurt_w, proj)
    return 0


def calc_rush_yds_proj(player_name, opp, team, spread, total,
                       hurt_pos_for_team, db):
    """
      calc rush yards
    """
    gamelogs = sqllite_utils.get_player_stats_sec(player_name, team,
                                                  const.RUSHING_KEY, db)

    if (len(gamelogs) <= 0):
        # print(f"Couldn't get game logs for:{player_name}")
        return None
    proj = get_weighted_mean(
        'yds', remove_outliers('yds', const.RUSHING_KEY, gamelogs))
    def_weight = get_weight_for_def(proj, opp, TOP_RB_D, WORST_RB_D,
                                    const.WORST_RB_D_YDS_WEIGHT,
                                    const.TOP_RB_D_YDS_WEIGHT)

    team_spread = float(spread.get(team))
    spread_weight = get_weight_for_spread(team_spread, const.RUSH_YDS_AT_S_W,
                                          proj)
    hurt_line_weight = _get_line_hurt_weight(team, hurt_pos_for_team, proj,
                                             const.LINE_HURT_WEIGHT_RUSH)
    proj += hurt_line_weight
    proj += spread_weight
    proj += def_weight
    return format_proj(proj)


def calc_rec_yds_proj(player_name, opp, team, spread, total, hurt_pos_for_team,
                      db):
    """
      Calc rec yards
    """
    gamelogs = sqllite_utils.get_player_stats_sec(player_name, team,
                                                  const.RECEIVING_KEY, db)
    if len(gamelogs) <= 0:
        # print(f"Couldn't get game logs for:{player_name}")
        return None
    proj = get_weighted_mean(
        'yds', remove_outliers('yds', const.RECEIVING_KEY, gamelogs))
    def_weight = get_weight_for_def(proj, opp, TOP_WR_D, WORST_WR_D,
                                    const.WORST_WR_D_YDS_WEIGHT,
                                    const.TOP_WR_D_YDS_WEIGHT)
    # print(f"{player_name} def: {def_weight}")
    # if player_name == "rex-burkhead":
    #     print(f"Chase: {def_weight} vs opp {opp}")

    qb_weight = get_weight_for_def(proj, opp, TOP_QB_D, WORST_QB_D,
                                   const.WORST_QB_D_REC_YDS_WEIGHT,
                                   const.TOP_QB_D_REC_YDS_WEIGHT)
    spread_weight = 0
    team_spread = float(spread.get(team))
    if total > AVG_TOTAL:
        spread_weight = get_weight_for_spread(team_spread,
                                              const.REC_YDS_HT_S_W, proj)
    else:
        spread_weight = get_weight_for_spread(team_spread,
                                              const.REC_YDS_LT_S_W, proj)
    hurt_line_weight = _get_line_hurt_weight(team, hurt_pos_for_team, proj,
                                             const.LINE_HURT_WEIGHT_REC)
    hurt_wr_weight = _get_wr_hurt_weight(team, hurt_pos_for_team, proj)

    proj += hurt_wr_weight
    proj += hurt_line_weight
    proj += qb_weight
    proj += def_weight
    proj += spread_weight
    return format_proj(proj)


def get_stats(player_gls):
    r"""
    :param player_gls gamelogs for a certain player
      Get list dictionary of stats from gamelog
    """
    year_stats = {YEARS[0]: [], YEARS[1]: []}
    for game in player_gls:
        year_stats[str(game.get('season_year'))].append(game)
    return year_stats


def get_win_loss_margin(gamelog):
    """
        Get the games win or lose margin from gamelog
    """
    result = gamelog.get('result')
    score_match = SCORE_REGEX.match(result)
    diff = abs(int(score_match.group(1)) - int(score_match.group(2)))
    if result.find('W') == 0:
        # win
        return diff
    elif result.find('L') == 0:
        # loss
        return -diff
    else:
        return 0


def get_total(gamelog):
    """
        Get game total
    """
    result = gamelog.get('result')
    score_match = SCORE_REGEX.match(result)
    return int(score_match.group(1)) + int(score_match.group(2))


# Mixon, Sinlgetary, Montgomery,
# TODO pull from database
# def calculate_stat_corr(player_for_team, stat_sec_key, stat_key):
#     """
#         score to yards
#         score to attempts
#     """

#     stats = []
#     scores = []
#     totals = []

#     gamelogs_for_player = scraper.get_player_gamelogs(player_for_team)
#     for _, gamelogs in gamelogs_for_player.items():
#         all_stats = get_stats(gamelogs, stat_sec_key)
#         for _, stat_sec in all_stats.items():
#             for stat_row in stat_sec:
#                 stats.append(float(stat_row.get(stat_key)))
#                 scores.append(get_win_loss_margin(stat_row))
#                 totals.append(get_total(stat_row))

#     stats = np.array(stats)
#     scores = np.array(scores)
#     totals = np.array(totals)

#     print(f"{stats} \n\n {scores} \n\n {totals}")

#     scores_corr = np.corrcoef(scores, stats)
#     totals_corr = np.corrcoef(totals, stats)
#     # plt.scatter(scores, stats)
#     # plt.show()

#     print(
#         f"Scores correlation matrix for {stat_sec_key} {stat_key}: \n\n {scores_corr} \n\n"
#     )
#     print(
#         f"Total correlation matrix for {stat_sec_key} {stat_key}: \n\n {totals_corr} \n\n"
#     )

# def calculate_defense_corr(player_for_team, stat_sec_key, stat_key,
#                            pos_top_d_ranking):
#     """
#         score to yards
#         score to attempts
#     """

#     stats = []
#     def_ranking = []

#     gamelogs_for_player = scraper.get_player_gamelogs(player_for_team)
#     for _, gamelogs in gamelogs_for_player.items():
#         all_stats = get_stats(gamelogs, stat_sec_key)
#         for _, stat_sec in all_stats.items():
#             for stat_row in stat_sec:
#                 stat = float(stat_row.get(stat_key))
#                 if stat > 0:
#                     stats.append(stat)
#                     def_ranking.append(
#                         pos_top_d_ranking.index(
#                             OPP_REGEX.match(stat_row.get("OPP")).group(2)))

#     stats = np.array(stats)
#     def_ranking = np.array(def_ranking)

#     # plt.scatter(def_ranking, stats)
#     # plt.show()

#     def_corr = np.corrcoef(def_ranking, stats)
#     print(
#         f"Defense correlation matrix for {stat_sec_key} {stat_key}: \n\n {def_corr} \n\n"
#     )
