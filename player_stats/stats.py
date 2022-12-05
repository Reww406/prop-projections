r"""
  Caclulate projections based on player stats..
"""

import pickle
import re
import statistics
import joblib
import numpy as np
from matplotlib import pyplot as plt
from player_stats import scraper, sqllite_utils
from player_stats import constants as const
import pandas as pd

# QB_D_STATS = scraper.get_pos_defense_ranking(
#     scraper.RANKING_FOR_POS_REGEX.get("qb"))
RB_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("rb"))
WR_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("wr"))
TE_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("te"))

# TOP_QB_D = scraper.get_top_n_def_for_pos(QB_D_STATS, 32, False)
# WORST_QB_D = scraper.get_top_n_def_for_pos(QB_D_STATS, 10, True)
TOP_RB_D = scraper.get_top_n_def_for_pos(RB_D_STATS, 5, False)
WORST_RB_D = scraper.get_top_n_def_for_pos(RB_D_STATS, 5, True)
TOP_WR_D = scraper.get_top_n_def_for_pos(WR_D_STATS, 5, False)
WORST_WR_D = scraper.get_top_n_def_for_pos(WR_D_STATS, 5, True)
# TODO Fix TE Defense..
TOP_TE_D = scraper.get_top_n_def_for_pos(TE_D_STATS, 5, False)
WORST_TE_D = scraper.get_top_n_def_for_pos(TE_D_STATS, 5, True)

SCORE_REGEX = re.compile(r"^[WLT]{1}(\d+)[\-]{1}(\d+).*?$")
OPP_REGEX = re.compile(r"^(@|vs)(\w+)$")

# Spread has big impact

CLOSE_NEG = -2.5
CLOSE_POS = 2.5
HIGH_SPREAD = 8
AVG_TOTAL = 46

YEARS = [const.CURRENT_YEAR, const.LAST_YEAR]

SEASON_KEY = {
    const.CURRENT_YEAR: const.SEASON_2022,
    const.LAST_YEAR: const.SEASON_2021
}

reciever_model = joblib.load("rec-pipeline.pkl")
# reciever_model = {}
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
    return proj * (float(weight) / 100.00)


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


def _get_close_spread_or_total(gamelogs, spread, total, db):
    games_between = []
    for log in gamelogs:
        opp = OPP_REGEX.match(log.get('opp')).group(2)
        odds = sqllite_utils.get_odds_for_game(log.get('season_year'),
                                               log.get('game_date'),
                                               log.get('team_int'), db)

        if odds is None:
            odds = sqllite_utils.get_odds_for_game(log.get('season_year'),
                                                   log.get('game_date'), opp,
                                                   db)
            if odds is None:
                continue
            prev_spread = odds.get('spread') * -1
            prev_total = odds.get('total')
        else:
            prev_spread = odds.get('spread')
            prev_total = odds.get('total')

        # if spread < 0:
        if total - 3.5 <= prev_total <= total + 3.5:
            games_between.append(log)
        elif spread - 2.5 <= prev_spread <= spread + 2.5:
            games_between.append(log)
    return games_between


def _get_avg_tgts_for_year(gamelogs, year):
    values = []
    for gl in gamelogs:
        if gl['season_year'] == year:
            values.append(gl['tgts'])
    return np.mean(values)

def get_inter_ats_prob(player_name, opp, team, spread, total, odds_num, pos_rank,
                     db):

def get_rec_ats_prob(player_name, opp, team, spread, total, odds_num, pos_rank,
                     db):
    """
        Returns percent time that player has hit the over
    """
    gamelogs = sqllite_utils.get_player_stats_sec(player_name, team,
                                                  const.RECEIVING_KEY, db)
    if pos_rank in ['WR1', 'TE1']:
        print('Big man')
        similar_games = gamelogs
    else:
        similar_games = _get_close_spread_or_total(gamelogs,
                                                   float(spread.get(team)),
                                                   total, db)
    # print(player_name)
    over_odds = 0.0
    over_20 = 0.0
    over_40 = 0.0
    over_60 = 0.0
    over_80 = 0.0
    total = len(similar_games)
    if total == 0:
        print("threw away")
        return None
    for game in similar_games:
        if game.get('yds') > odds_num:
            over_odds += 1.0
        if game.get('yds') > 20:
            over_20 += 1.0
        if game.get('yds') > 40:
            over_40 += 1.0
        if game.get('yds') > 60:
            over_60 += 1.0
        if game.get('yds') > 80:
            over_80 += 1.0

    results = [(over_20 / total) * 100, (over_40 / total) * 100,
               (over_60 / total) * 100, (over_80 / total) * 100,
               (over_odds / total) * 100]

    avg_tgts = _get_avg_tgts_for_year(gamelogs, 2022)
    # Boost 3%
    if avg_tgts <= 3.8:
        print("threw away tgts")
        return None
    if pos_rank == 'TE1':
        print("TE")
        if opp in TOP_TE_D:
            for result in results:
                if result <= 90:
                    result -= 3

        if opp in WORST_TE_D:
            for result in results:
                if result <= 90:
                    result += 3
    else:
        if opp in TOP_WR_D:
            for result in results:
                if result <= 90:
                    result -= 3

        if opp in WORST_WR_D:
            for result in results:
                if result <= 90:
                    result += 3

    if avg_tgts >= 6.5:
        print("BIG Target")
        for result in results:
            if result <= 90:
                result += 2.5

    if total > 0:
        return {
            "20+": "{:.1f}%".format(results[0]),
            "40+": "{:.1f}%".format(results[1]),
            "60+": "{:.1f}%".format(results[2]),
            "80+": "{:.1f}%".format(results[3]),
            "over": "{:.1f}%".format(results[4])
        }
    else:
        return {"20+": 0, "40+": 0, "60+": 0, "80+": 0, "over": 0}


def get_rush_ats_prob(player_name, opp, team, spread, total, odds_num,
                      pos_rank, db):
    """
        Returns percent time that player has hit the over
    """
    gamelogs = sqllite_utils.get_player_stats_sec(player_name, team,
                                                  const.RUSHING_KEY, db)

    # similar_games = _get_close_spread_or_total(gamelogs,
    #                                            float(spread.get(team)), total,
    #                                            db)

    similar_games = gamelogs

    over_odds = 0.0
    over_20 = 0.0
    over_40 = 0.0
    over_60 = 0.0
    over_80 = 0.0
    total = len(similar_games)
    for game in similar_games:
        if game.get('yds') > odds_num:
            over_odds += 1.0
        if game.get('yds') > 20:
            over_20 += 1.0
        if game.get('yds') > 40:
            over_40 += 1.0
        if game.get('yds') > 60:
            over_60 += 1.0
        if game.get('yds') > 80:
            over_80 += 1.0

    if total == 0:
        print("threw away")
        return None
    results = [(over_20 / total) * 100, (over_40 / total) * 100,
               (over_60 / total) * 100, (over_80 / total) * 100,
               (over_odds / total) * 100]

    if opp in TOP_RB_D:
        for result in results:
            if result <= 90:
                result -= 3

    if opp in WORST_RB_D:
        for result in results:
            if result <= 90:
                result += 3

    if total > 0:
        return {
            "20+": "{:.1f}%".format(results[0]),
            "40+": "{:.1f}%".format(results[1]),
            "60+": "{:.1f}%".format(results[2]),
            "80+": "{:.1f}%".format(results[3]),
            "over": "{:.1f}%".format(results[4])
        }
    else:
        return {"20+": 0, "40+": 0, "60+": 0, "80+": 0, "over": 0}


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