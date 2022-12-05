# from player_stats import stats
from concurrent.futures import ThreadPoolExecutor
import copy
import json
import pickle
import re
import time
import joblib
from sklearn import svm

from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler, scale
from sklearn.utils import column_or_1d
from player_stats import scraper
import numpy as np
import pandas as pd

from scipy.stats import uniform
from player_stats import constants as const
from player_stats import sqllite_utils
from player_stats import stats
from sklearn.neural_network import MLPRegressor
import main

# Regular prediction, top_wr_d, worst_wr_d, top_qb_d, worst_qb_d, team_spread, total, line_hurt, wr_hurt
# def build_df(db):
#     game_dict = {
#         "proj": [],
#         "wr_d_rank": [],
#         # "worst_wr_d": [],
#         "qb_d_rank": [],
#         # "worst_qb_d": [],
#         "team_spread": [],
#         "total": [],
#         # "line_hurt": [],
#         # "wr_hurt": [],
#         "actual_stat": []
#     }

#     for i in range(1, 5):
#         f = open(f"test_props/combined-{i}.txt", 'r', encoding='UTF-8')
#         current_prop_lines, current_game, current_spread, current_total = [], "", None, 0
#         team_pos = {}
#         for line in f:
#             game_match = main.GAME_REGEX.match(line)
#             total_match = main.TOTAL_REGEX.match(line)
#             spread_match = main.SPREAD_REGEX.match(line)
#             date_match = main.DATE_REGEX.match(line)
#             hurt_pos = main.HURT_PLAYER_RE.match(line)
#             if len(line.strip()) == 0:
#                 continue
#             if bool(hurt_pos):
#                 if team_pos.get(hurt_pos.group(1)) is None:
#                     team_pos[hurt_pos.group(1)] = [hurt_pos.group(2)]
#                 else:
#                     team_pos[hurt_pos.group(1)].append(hurt_pos.group(2))
#                 continue
#             if bool(date_match):
#                 game_date = date_match.group(1)
#                 continue
#             if bool(total_match):
#                 current_total = float(total_match.group(1).strip())
#                 continue
#             if bool(spread_match):
#                 current_spread = json.loads(
#                     spread_match.group(1).replace("'", '"').strip())
#                 continue
#             if bool(game_match):
#                 # print(f"Found game: {game_match.group(0)}")
#                 if len(current_game) > 0 and current_game != game_match.group(
#                         0):
#                     # Not the first game found..
#                     process_prop(current_prop_lines, game_dict, current_game,
#                                  current_spread, current_total, team_pos,
#                                  game_date, db)
#                     current_prop_lines = []
#                     team_pos = {}
#                     current_game = game_match.group(0).strip()
#                 elif current_game != game_match.group(0):
#                     # First game in file
#                     current_game = game_match.group(0)
#             else:
#                 # if nothing else then prop line..
#                 if line.split(",")[1].strip() == 'TNF':
#                     # print("Skipping TNF")
#                     continue
#                 current_prop_lines.append(line)
#     for key, value in game_dict.items():
#         print(f"{key} : {len(value)}")
#     return pd.DataFrame(game_dict)

OPP_REGEX = re.compile(r"^(@|vs)(\w+)$")


def get_all_games(table, db):
    r"""
      Processes a prop line from prop list gets opponent and
      projection
    """

    all_gls = sqllite_utils.get_all_game_logs(const.RECEIVING_KEY, db)
    print(len(all_gls))
    for gl in all_gls:
        opp = OPP_REGEX.match(gl['opp']).group(2)
        player_game_logs = sqllite_utils.get_player_stats_sec(
            gl.get('player_name'), gl.get("team_int"), const.RECEIVING_KEY, db)

        if len(player_game_logs) <= 0:
            # print(f"Couldn't get game logs for:{player_name}")
            continue
        odds = sqllite_utils.get_odds_for_game(gl.get('season_year'),
                                               gl.get('game_date'),
                                               gl.get('team_int'), db)
        if odds is None:
            continue

        yds_proj = stats.get_weighted_mean(
            'yds',
            stats.remove_outliers('yds', const.RECEIVING_KEY,
                                  player_game_logs))
        tgts_proj = stats.get_weighted_mean(
            'tgts',
            stats.remove_outliers('tgts', const.RECEIVING_KEY,
                                  player_game_logs))

        table.get('proj').append(yds_proj)

        # if opp in stats.TOP_WR_D:
        table.get('wr_d_rank').append(stats.TOP_WR_D.index(opp) + 1)

        table.get('qb_d_rank').append(stats.TOP_QB_D.index(opp) + 1)
        table.get('team_spread').append(odds.get('spread'))
        table.get('total').append(odds.get('total'))

        table.get('actual_stat').append(gl.get('yds'))


conn = sqllite_utils.get_db_in_mem()
game_dict = {
    "proj": [],
    "wr_d_rank": [],
    # "worst_wr_d": [],
    "qb_d_rank": [],
    # "worst_qb_d": [],
    "team_spread": [],
    "total": [],
    # "line_hurt": [],
    # "wr_hurt": [],
    "actual_stat": []
}
get_all_games(game_dict, conn)
print(len(game_dict['proj']))
# for i in range(0, 100):
#     print(
#         f"P: {game_dict.get('proj')[i]} D: {game_dict.get('qb_d_rank')[i]} Spread: {game_dict.get('team_spread')[i]} Total {game_dict.get('total')[i]} AS {game_dict.get('actual_stat')[i]}"
#     )
df = pd.DataFrame(game_dict)
target_col = ['actual_stat']
predictors = list(set(list(df.columns)) - set(target_col))

X = df[predictors].values
y = column_or_1d(df[target_col].values)

x_train, x_test, y_train, y_test = train_test_split(X,
                                                    y,
                                                    test_size=0.25,
                                                    random_state=42)
print(x_train.shape)
print(x_test.shape)

scaler = StandardScaler()

mlp = MLPRegressor(random_state=42,
                   hidden_layer_sizes=(10, ),
                   solver='adam',
                   max_iter=3000,
                   learning_rate_init=0.0001,
                   activation='relu')

distributions = {
    "mlp__activation": ['relu'],
    "mlp__solver": ['lbfgs', 'adam', 'spg'],
    "mlp__max_iter": [500, 1000, 2000, 5000, 10000],
    "mlp__learning_rate_init":
    [0.001, 0.01, 0.05, 0.002, 0.025, 0.1, 0.050, 0.0001],
    "mlp__hidden_layer_sizes": [(i, ) for i in range(0, 100, 5)]
}

pipe = Pipeline([('scaler', MinMaxScaler()), ('mlp', mlp)])
pipe.fit(x_train, y_train)
# print(x_train[0])
# scaler.fit(x_train)
# x_train = scaler.transform(x_train)
# x_test = scaler.transform(x_test)

clf = RandomizedSearchCV(pipe, distributions, random_state=1)
# mlp.fit(x_train, y_train)
# search = clf.fit(x_train, y_train)
# print(search.best_params_)

print(len(x_test))
print(pipe.score(x_test, y_test))
print(pipe.predict(
    np.array([
        88.51076561,
        23,
        20,
        -14.5,
        40,
    ]).reshape(1, -1)))

# # joblib.dump(pipe, 'rec-pipeline.pkl')
