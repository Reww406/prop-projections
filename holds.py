import datetime
import re

import numpy as np
from player_stats import scraper, sqllite_utils
import pandas as pd
# pos_odds = 110

# neg_odds = 135.0
# neg_be = (neg_odds / (100.0 + neg_odds) * 100)

# hold = (pos_be + neg_be) - 100.0

# print(f"-{neg_odds} BE: {neg_be} {pos_odds} BE: {pos_be} Hold = {hold}")

# test = 'DET starting LG out\n'
# HURT_PLAYER_RE = re.compile(r"^(\w{2,3})\sstarting\s(\w{1,2}).*?$",
#                             re.IGNORECASE)

# match = HURT_PLAYER_RE.match(test)

# print(match.group(2))
# string = "ATL FalconsATLAR Commanders"
# last_pos = last_position = string.rfind('AT')
# string = string[:last_position] + "@" + string[last_position + 2:]
# print(string)

neg_odds = 195
print((neg_odds / (100.0 + neg_odds) * 100))

pos_odds = 130
print(100 / (100 + pos_odds) * 100)

# team_name_to_int_special = {
#     'Washington Football Team': 'WSH',
#     'Washington Redskins': 'WSH',
#     'Oakland Raiders': 'LV'
# }
# years = [2019]

# day_of_week = {
#     0: 'Mon',
#     1: 'Tue',
#     2: 'Wed',
#     3: 'Thu',
#     4: 'Fri',
#     5: 'Sat',
#     6: 'Sun'
# }

# def load_historical_odds(filename, cur):
#     df = pd.read_csv(filename)
#     print(df.columns)

#     # Store home team
#     for _, row in df.iterrows():
#         date = row['Date']
#         season_year = int(date[:date.find("-")])
#         month = int(date[date.find("-") + 1:date.find("-",
#                                                       date.find("-") + 1)])
#         day = int(date[date.rfind("-") + 1:])
#         dow_num = datetime.datetime(season_year, month, day).weekday()
#         game_date = f"{day_of_week.get(dow_num)} {month}/{day}"

#         if season_year in years:
#             home_int = scraper.TEAM_NAME_TO_INT.get(row['Home Team'])
#             if home_int is None:
#                 # print(row['Home Team'])
#                 home_int = team_name_to_int_special.get(row['Home Team'])
#             home_spread = row['Home Line Close']

#             away_int = scraper.TEAM_NAME_TO_INT.get(row['Away Team'])
#             if away_int is None:
#                 # print(row['Away Team'])
#                 away_int = team_name_to_int_special.get(row['Away Team'])

#             away_spread = row['Away Line Close']

#             total_over = row['Total Score Close']

#             sqllite_utils.insert_historical_odds(season_year, game_date,
#                                                  home_int, total_over,
#                                                  home_spread, cur)
#             sqllite_utils.insert_historical_odds(season_year, game_date,
#                                                  away_int, total_over,
#                                                  away_spread, cur)

# load_historical_odds("nfl_odds.csv", sqllite_utils.get_conn())

# print(scraper.get_starting_pos(['WSH'], ['WR']))

# date = 'Sun 1/3'
# JAN_REGEX = re.compile(r"^\w{3}\s([1])/.*?$")
# print(JAN_REGEX.match(date).group(1))
scraper.driver_quit()
conn = sqllite_utils.get_conn()

targets = conn.execute("SELECT tgts FROM player_rec_gl").fetchall()
values = [target['tgts'] for target in targets]
print(np.mean(values))
