# from player_stats import stats
from concurrent.futures import ThreadPoolExecutor
import copy
import time
from player_stats import scraper
import numpy as np

from random import randint
from player_stats import constants as const
from player_stats import sqllite_utils
import main

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


def rand(weight):
    diff = 10
    return randint(weight - diff, weight + diff)


def rand_with_diff(weight, diff):
    return randint(weight - diff, weight + diff)


def pos_rand(weight):
    diff = 20
    return randint(weight, weight + diff)


def randomize_weights():
    # 21
    const.LAST_Y_STAT_W = 55
    const.BLOW_OUT_STAT_W = 52
    const.THIS_YEAR_STAT_W = 149
    const.TOP_RB_D_YDS_WEIGHT = rand(-30)
    const.WORST_RB_D_YDS_WEIGHT = pos_rand(0)
    const.WORST_QB_D_REC_YDS_WEIGHT = pos_rand(0)
    const.WORST_WR_D_YDS_WEIGHT = pos_rand(0)
    const.TOP_QB_D_REC_YDS_WEIGHT = rand(-30)
    const.TOP_WR_D_YDS_WEIGHT = rand(-18)
    # [very underdog, very fav, slight underdog, slight fav, close game]
    const.RUSH_YDS_AT_S_W = [rand(0), rand(0), rand(0), rand(0), rand(0)]
    const.REC_YDS_HT_S_W = [
        rand(0), rand(0), rand(0),
        rand(0), rand(0), rand(0)
    ]
    const.REC_YDS_LT_S_W = [rand(0), rand(0), rand(0), rand(0), rand(0)]
    const.STARTING_WR_HURT_WEIGHT = rand(-10)
    const.LINE_HURT_WEIGHT_REC = rand(-10)
    const.LINE_HURT_WEIGHT_RUSH = rand(-30)


best_top_qb_d_rec_yds_weight = 0
best_worst_qb_d_rec_yds_weight = 0
best_top_rb_d_yds_weights = 0
best_worst_rb_d_yds_weights = 0
best_top_wr_d_yds_weights = 0
best_worst_wr_d_yds_weight = 0
best_line_hurt_weight_rush = 0
best_line_hurt_weight_rec = 0
best_starting_wr_hurt_weight = 0
best_last_y_stat_w = 0
best_this_year_stat_w = 0
best_blow_out_stat_w = 0
best_rush_yds_at_s_w = [0, 0, 0, 0, 0]
best_rec_yds_ht_s_w = [0, 0, 0, 0, 0]
best_rec_yds_lt_s_w = [0, 0, 0, 0, 0]

# con = sqllite_utils.get_db_in_mem()


def _process_prop_file(prop_array, con):

    results = main.create_report(prop_array, main.calculate_error_per, False,
                                 con)
    return results


def load_prop_file_into_memory(file_name):
    prop_file = open(file_name, 'r', encoding='UTF-8')
    lines = []
    for line in prop_file:
        lines.append(line)
    prop_file.close()
    return lines


#
# Single weight
#
try:
    print_points = [i * 1000 for i in range(0, 100)]
    lowest_error = 100
    conn = sqllite_utils.get_db_in_mem()
    start_time = epoch_time = int(time.time())
    files = []
    connections = []
    # for i in range(0, 4):
    #     connections.append(sqllite_utils.get_db_in_mem())
    for i in range(1, 5):
        files.append(
            load_prop_file_into_memory(f"test_props/combined-{i}.txt"))
    with ThreadPoolExecutor(max_workers=5) as executor:
        for i in np.arange(0, 100000, 1):
            randomize_weights()
            results_per = []
            futures = []
            # print(const.THIS_YEAR_STAT_W)
            for file_num in range(0, 4):
                # futures.append(
                #     executor.submit(_process_prop_file, files[file_num],
                #                     connections[file_num]))
                results_per.append(_process_prop_file(files[file_num], conn))
            # for future in futures:
            #     results_per.append(future.result())

            total_error_per = float("%.3f" % np.mean(results_per))
            if i in print_points:
                print(f"Took: {(int(time.time()) - start_time)/60}")
                print(f"At: {i}")
            # print(f"{total_error_per}")
            if total_error_per <= lowest_error:
                print(f"new lowest error: {total_error_per}")
                lowest_error = total_error_per
                best_top_qb_d_rec_yds_weight = const.TOP_QB_D_REC_YDS_WEIGHT
                best_worst_qb_d_rec_yds_weight = const.WORST_QB_D_REC_YDS_WEIGHT
                best_top_rb_d_yds_weights = const.TOP_RB_D_YDS_WEIGHT
                best_worst_rb_d_yds_weights = const.WORST_RB_D_YDS_WEIGHT
                best_top_wr_d_yds_weights = const.TOP_WR_D_YDS_WEIGHT
                best_worst_wr_d_yds_weight = const.WORST_WR_D_YDS_WEIGHT
                best_line_hurt_weight_rush = const.LINE_HURT_WEIGHT_RUSH
                best_line_hurt_weight_rec = const.LINE_HURT_WEIGHT_REC
                best_starting_wr_hurt_weight = const.STARTING_WR_HURT_WEIGHT
                best_last_y_stat_w = const.LAST_Y_STAT_W
                best_this_year_stat_w = const.THIS_YEAR_STAT_W
                best_blow_out_stat_w = const.BLOW_OUT_STAT_W
                best_rush_yds_at_s_w = const.RUSH_YDS_AT_S_W
                best_rec_yds_ht_s_w = const.REC_YDS_HT_S_W
                best_rec_yds_lt_s_w = const.REC_YDS_LT_S_W
                # print(f"""best Top QB D REC YDS: {best_top_qb_d_rec_yds_weight}
                #         Worst QB D REC YDS {best_worst_qb_d_rec_yds_weight}
                #         Top rb d yds {best_top_rb_d_yds_weights}
                #         Worst rb d yds {best_worst_rb_d_yds_weights}
                #         top wr d {best_top_wr_d_yds_weights}
                #         worst wr d {best_worst_wr_d_yds_weight}
                #         line hurt rush {best_line_hurt_weight_rush}
                #         line hurt rec {best_line_hurt_weight_rec}
                #         starting wr out {best_starting_wr_hurt_weight}
                #         last y weight {best_last_y_stat_w}
                #         this y weight {best_this_year_stat_w}
                #         blowout weight {best_blow_out_stat_w}
                #         rush yds spread {best_rush_yds_at_s_w}
                #         lt rec yards {best_rec_yds_lt_s_w}
                #         ht rec yards {best_rec_yds_ht_s_w}""")
finally:
    print(f"""best Top QB D REC YDS: {best_top_qb_d_rec_yds_weight}
            Worst QB D REC YDS {best_worst_qb_d_rec_yds_weight}
            Top rb d yds {best_top_rb_d_yds_weights}
            Worst rb d yds {best_worst_rb_d_yds_weights}
            top wr d {best_top_wr_d_yds_weights}
            worst wr d {best_worst_wr_d_yds_weight}
            line hurt rush {best_line_hurt_weight_rush}
            line hurt rec {best_line_hurt_weight_rec}
            starting wr out {best_starting_wr_hurt_weight}
            last y weight {best_last_y_stat_w}
            this y weight {best_this_year_stat_w}
            blowout weight {best_blow_out_stat_w}
            rush yds spread {best_rush_yds_at_s_w}
            lt rec yards {best_rec_yds_lt_s_w}
            ht rec yards {best_rec_yds_ht_s_w}""")
# for file_num in range(1, 5):
#     prop_file = open(f"test_props/rec-yds-{file_num}.txt",
#                      'r',
#                      encoding='UTF-8')
#     results_per.append(
#         main.create_report(prop_file, main.calculate_error_per, False))
#     prop_file.close()
# total_error_per = np.mean(results_per)

# print(f"Best weight {best_weight} new score {total_error_per}")

#
# Spread Weight
#
# best_weights = [0, 0, 0, 0, 0]
# top_score = prev_score
# best_weight = 0
# for x in np.arange(0, 5):
#     top_score = prev_score
#     best_weight = 0
#     print("next weight")
#     for i in np.arange(40, -40, -0.25):
#         results_per = []
#         const.REC_YDS_LT_S_W[x] = i
#         # print(const.RUSH_YDS_AT_S_W)
#         for file_num in range(1, 5):
#             prop_file = open(f"test_props/rec-yds-{file_num}.txt",
#                              'r',
#                              encoding='UTF-8')
#             results_per.append(
#                 main.create_report(prop_file, main.calculate_correct_per,
#                                    False))
#             prop_file.close()
#         total_cor = np.mean(results_per)
#         if total_cor >= top_score:
#             if total_cor == top_score:
#                 if abs(i) < abs(best_weight):
#                     top_score = total_cor
#                     best_weight = i
#                     print(f"new top score {top_score} weights: {best_weight}")
#             else:
#                 top_score = total_cor
#                 best_weight = i
#                 print(f"new top score {top_score} weights: {best_weight}")
#         const.REC_YDS_LT_S_W[x] = 0
#         best_weights[x] = best_weight

# results_per = []
# for file_num in range(1, 5):
#     prop_file = open(f"test_props/rec-yds-{file_num}.txt",
#                      'r',
#                      encoding='UTF-8')
#     results_per.append(
#         main.create_report(prop_file, main.calculate_correct_per, False))
#     prop_file.close()
# prev_score = np.mean(results_per)
# print(f"Total score no change: {prev_score}")

# #
# # Spread Weight
# #
# # best_weights = [0, 0, 0, 0, 0]
# # top_score = prev_score
# # best_weight = 0
# # for x in np.arange(0, 5):
# #     top_score = prev_score
# #     best_weight = 0
# #     print("next weight")
# #     for i in np.arange(40, -40, -0.25):
# #         results_per = []
# #         const.REC_YDS_LT_S_W[x] = i
# #         # print(const.RUSH_YDS_AT_S_W)
# #         for file_num in range(1, 5):
# #             prop_file = open(f"test_props/rec-yds-{file_num}.txt",
# #                              'r',
# #                              encoding='UTF-8')
# #             results_per.append(
# #                 main.create_report(prop_file, main.calculate_correct_per,
# #                                    False))
# #             prop_file.close()
# #         total_cor = np.mean(results_per)
# #         if total_cor >= top_score:
# #             if total_cor == top_score:
# #                 if abs(i) < abs(best_weight):
# #                     top_score = total_cor
# #                     best_weight = i
# #                     print(f"new top score {top_score} weights: {best_weight}")
# #             else:
# #                 top_score = total_cor
# #                 best_weight = i
# #                 print(f"new top score {top_score} weights: {best_weight}")
# #         const.REC_YDS_LT_S_W[x] = 0
# #         best_weights[x] = best_weight

# #
# # Single weight
# #
# best_weight = 0
# top_score = prev_score
# print(prev_score)
# for i in np.arange(-35, 35, 0.25):
#     results_per = []
#     const.LINE_HURT_WEIGHT_RUSH = i
#     # print(const.THIS_YEAR_STAT_W)
#     for file_num in range(1, 5):
#         prop_file = open(f"test_props/rec-yds-{file_num}.txt",
#                          'r',
#                          encoding='UTF-8')
#         results_per.append(
#             main.create_report(prop_file, main.calculate_correct_per, False))
#         prop_file.close()
#     total_cor = np.mean(results_per)
#     # print(f"{total_cor} : {const.LINE_HURT_WEIGHT_REC}")
#     if total_cor >= top_score:
#         if total_cor == top_score:
#             if abs(i) < abs(best_weight):
#                 top_score = total_cor
#                 best_weight = i
#                 print(f"new top score {top_score} weights: {best_weight}")
#         else:
#             top_score = total_cor
#             best_weight = i
#             print(f"new top score {top_score} weights: {best_weight}")

# results_per = []
# const.LINE_HURT_WEIGHT_RUSH = best_weight
# for file_num in range(1, 5):
#     prop_file = open(f"test_props/rec-yds-{file_num}.txt",
#                      'r',
#                      encoding='UTF-8')
#     results_per.append(
#         main.create_report(prop_file, main.calculate_correct_per, False))
#     prop_file.close()
# prev_score = np.mean(results_per)
# # print(f"Results per: {results_per}")
# total_cor = np.mean(results_per)
# prop_file.close()

# print(f"Best weight {best_weight} new score {total_cor}")