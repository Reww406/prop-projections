from player_stats import stats
from player_stats import scraper
import numpy as np

running_backs = {
    'CIN': 'J. Mixon',
    'BUF': 'D. Singletary',
    'CHI': 'D. Montgomery',
    'TEN': 'D. Henry',
    'TB': 'L. Fournette',
    'CAR': 'D. Foreman',
    'LV': 'J. Jacobs',
    'CLE': 'N. Chubb'
}

quaterbacks = {
    'KC': 'P. Mahomes',
    'PHI': 'J. Hurts',
    'CLE': 'J. Brissett',
    'ATL': 'M. Mariota',
    'BUF': 'J. Allen',
    'SEA': 'G. Smith',
    'JAX': 'T. Lawrence',
    'TEN': 'R. Tannehill'
}

recievers = {
    'BUF': 'S. Diggs',
    'SF': 'B. Aiyuk',
    'TEN': 'R. Woods',
    'PIT': 'D. Johnson',
    'NO': 'C. Olave',
    'LAR': 'C. Kupp',
    'CLE': 'A. Cooper',
    'LAC': 'M. Williams'
}

# Use percentiles or MAD which is a more robust approximatin
# TODO try IQR on with more stats..
# def remove_outliers(stat_key, sec_key, gamelogs):
#     r"""
#         :param stat_key = YDS, ATT, CMP, REC
#         :param sec_key = Passing, Rushing or Recieving
#         :param gamelogs = the players game logs
#         Removes values X signma away from the mean.
#         year: [stats]
#     """
#     stat_section = get_stats(gamelogs, sec_key)
#     values = remove_non_starts(stat_key, sec_key, stat_section)
#     values = np.array(values)
#     values.sort()
#     if len(values) <= 1:
#         # Can't get mean if it's one stat...
#         return stat_section
#     mean = np.mean(values)
#     std = np.std(values)
#     new_stat_sec = {}
#     for year, year_stats in stat_section.items():
#         if year_stats is None:
#             continue
#         outliers_removed = []
#         for game_log in year_stats:
#             stat = float(game_log.get(stat_key))
#             z = (stat - mean) / std
#             if z < -2.0 or z > 2.0:
#                 print(f"Removing outlier: {stat}")
#             else:
#                 outliers_removed.append(game_log)
#         new_stat_sec[year] = outliers_removed
#     return new_stat_sec

TOP_PASS_D_ATT_WEIGHT = -8
WORST_PASS_D_ATT_WEIGHT = 8

QB_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("qb"))
RB_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("rb"))
WR_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("wr"))
TE_D_STATS = scraper.get_pos_defense_ranking(
    scraper.RANKING_FOR_POS_REGEX.get("te"))

TOP_QB_D = scraper.get_top_n_def_for_pos(QB_D_STATS, 32, False)
TOP_RB_D = scraper.get_top_n_def_for_pos(RB_D_STATS, 32, False)
TOP_WR_D = scraper.get_top_n_def_for_pos(WR_D_STATS, 32, False)
# TOP_TE_D = scraper.get_top_n_def_for_pos(TE_D_STATS, 32, False)

scraper.driver_quit()

# stats.calculate_stat_corr(running_backs, 'Rushing', 'YDS')
# stats.calculate_stat_corr(running_backs, 'Rushing', 'ATT')

# stats.calculate_stat_corr(quaterbacks, 'Passing', 'YDS')
# stats.calculate_stat_corr(quaterbacks, 'Passing', 'ATT')
# stats.calculate_stat_corr(quaterbacks, 'Passing', 'CMP')

# stats.calculate_stat_corr(recievers, 'Receiving', 'YDS')
# stats.calculate_stat_corr(recievers, 'Receiving', 'REC')

acc = [
    57, 57, 73, 59, 61, 72, 53, 73, 33, 65, 71, 55, 94, 50, 52, 57, 64, 52, 54,
    64, 92, 52
]
acc = np.array(acc).mean()
print(TOP_QB_D)
stats.calculate_defense_corr(quaterbacks, 'Passing', 'YDS', TOP_QB_D)
stats.calculate_defense_corr(quaterbacks, 'Passing', 'ATT', TOP_QB_D)
stats.calculate_defense_corr(quaterbacks, 'Passing', 'CMP', TOP_QB_D)

stats.calculate_defense_corr(running_backs, 'Rushing', 'YDS', TOP_RB_D)
stats.calculate_defense_corr(running_backs, 'Rushing', 'ATT', TOP_RB_D)

stats.calculate_defense_corr(recievers, 'Receiving', 'YDS', TOP_WR_D)
stats.calculate_defense_corr(recievers, 'Receiving', 'REC', TOP_WR_D)