import math
import pytest
import re
import numpy as np
from scipy import stats
import statistics

spread_regex = re.compile(r"^([\-\+]{1}[\d]+\.?[5]?).*?$")
game_logs = {
    '2022': [{
        'CMP': '27',
        'ATT': '38',
        'YDS': '238',
        'CMP%': '71.1',
        'AVG': '6.3',
        'TD': '2',
        'INT': '0',
        'LNG': '22',
        'SACK': '3',
        'RTG': '104.9',
        'QBR': '62.0',
        'Result': 'W27-22',
        'OPP': '@TB'
    }, {
        'CMP': '9',
        'ATT': '16',
        'YDS': '120',
        'CMP%': '56.3',
        'AVG': '7.5',
        'TD': '0',
        'INT': '0',
        'LNG': '31',
        'SACK': '3',
        'RTG': '80.2',
        'QBR': '47.0',
        'Result': 'W23-20',
        'OPP': 'vsCLE'
    }, {
        'CMP': '17',
        'ATT': '32',
        'YDS': '210',
        'CMP%': '53.1',
        'AVG': '6.6',
        'TD': '1',
        'INT': '1',
        'LNG': '19',
        'SACK': '2',
        'RTG': '71.1',
        'QBR': '60.2',
        'Result': 'L24-20',
        'OPP': '@NYG'
    }, {
        'CMP': '19',
        'ATT': '32',
        'YDS': '174',
        'CMP%': '59.4',
        'AVG': '5.4',
        'TD': '1',
        'INT': '1',
        'LNG': '21',
        'SACK': '1',
        'RTG': '71.6',
        'QBR': '29.6',
        'Result': 'W19-17',
        'OPP': 'vsCIN'
    }, {
        'CMP': '20',
        'ATT': '29',
        'YDS': '144',
        'CMP%': '69.0',
        'AVG': '5.0',
        'TD': '1',
        'INT': '2',
        'LNG': '21',
        'SACK': '2',
        'RTG': '63.0',
        'QBR': '47.7',
        'Result': 'L23-20',
        'OPP': 'vsBUF'
    }, {
        'CMP': '18',
        'ATT': '29',
        'YDS': '218',
        'CMP%': '62.1',
        'AVG': '7.5',
        'TD': '4',
        'INT': '1',
        'LNG': '35',
        'SACK': '4',
        'RTG': '110.3',
        'QBR': '87.8',
        'Result': 'W37-26',
        'OPP': '@NE'
    }, {
        'CMP': '21',
        'ATT': '29',
        'YDS': '318',
        'CMP%': '72.4',
        'AVG': '11.0',
        'TD': '3',
        'INT': '0',
        'LNG': '75',
        'SACK': '0',
        'RTG': '142.6',
        'QBR': '82.8',
        'Result': 'L42-38',
        'OPP': 'vsMIA'
    }, {
        'CMP': '17',
        'ATT': '30',
        'YDS': '213',
        'CMP%': '56.7',
        'AVG': '7.1',
        'TD': '3',
        'INT': '1',
        'LNG': '55',
        'SACK': '2',
        'RTG': '98.4',
        'QBR': '74.4',
        'Result': 'W24-9',
        'OPP': '@NYJ'
    }],
    '2021': [{
        'CMP': '4',
        'ATT': '4',
        'YDS': '17',
        'CMP%': '100.0',
        'AVG': '4.3',
        'TD': '0',
        'INT': '0',
        'LNG': '11',
        'SACK': '1',
        'RTG': '84.4',
        'QBR': '9.3',
        'Result': 'L24-22',
        'OPP': '@CLE'
    }, {
        'CMP': '23',
        'ATT': '37',
        'YDS': '253',
        'CMP%': '62.2',
        'AVG': '6.8',
        'TD': '1',
        'INT': '1',
        'LNG': '29',
        'SACK': '7',
        'RTG': '80.1',
        'QBR': '55.4',
        'Result': 'L20-19',
        'OPP': '@PIT'
    }, {
        'CMP': '20',
        'ATT': '32',
        'YDS': '165',
        'CMP%': '62.5',
        'AVG': '5.2',
        'TD': '1',
        'INT': '4',
        'LNG': '39',
        'SACK': '2',
        'RTG': '46.5',
        'QBR': '33.6',
        'Result': 'W16-10',
        'OPP': 'vsCLE'
    }, {
        'CMP': '26',
        'ATT': '43',
        'YDS': '238',
        'CMP%': '60.5',
        'AVG': '5.5',
        'TD': '1',
        'INT': '1',
        'LNG': '30',
        'SACK': '4',
        'RTG': '73.6',
        'QBR': '48.9',
        'Result': 'L22-10',
        'OPP': '@MIA'
    }, {
        'CMP': '27',
        'ATT': '41',
        'YDS': '266',
        'CMP%': '65.9',
        'AVG': '6.5',
        'TD': '3',
        'INT': '2',
        'LNG': '22',
        'SACK': '3',
        'RTG': '88.0',
        'QBR': '52.5',
        'Result': 'W34-31 OT',
        'OPP': 'vsMIN'
    }, {
        'CMP': '15',
        'ATT': '31',
        'YDS': '257',
        'CMP%': '48.4',
        'AVG': '8.3',
        'TD': '1',
        'INT': '0',
        'LNG': '39',
        'SACK': '5',
        'RTG': '87.7',
        'QBR': '49.8',
        'Result': 'L41-17',
        'OPP': 'vsCIN'
    }, {
        'CMP': '19',
        'ATT': '27',
        'YDS': '167',
        'CMP%': '70.4',
        'AVG': '6.2',
        'TD': '1',
        'INT': '2',
        'LNG': '21',
        'SACK': '3',
        'RTG': '68.0',
        'QBR': '59.1',
        'Result': 'W34-6',
        'OPP': 'vsLAC'
    }, {
        'CMP': '37',
        'ATT': '43',
        'YDS': '442',
        'CMP%': '86.1',
        'AVG': '10.3',
        'TD': '4',
        'INT': '0',
        'LNG': '43',
        'SACK': '2',
        'RTG': '140.5',
        'QBR': '83.9',
        'Result': 'W31-25 OT',
        'OPP': 'vsIND'
    }, {
        'CMP': '22',
        'ATT': '37',
        'YDS': '316',
        'CMP%': '59.5',
        'AVG': '8.5',
        'TD': '1',
        'INT': '0',
        'LNG': '49',
        'SACK': '3',
        'RTG': '96.2',
        'QBR': '70.8',
        'Result': 'W23-7',
        'OPP': '@DEN'
    }, {
        'CMP': '16',
        'ATT': '31',
        'YDS': '287',
        'CMP%': '51.6',
        'AVG': '9.3',
        'TD': '1',
        'INT': '1',
        'LNG': '41',
        'SACK': '4',
        'RTG': '81.0',
        'QBR': '49.2',
        'Result': 'W19-17',
        'OPP': '@DET'
    }, {
        'CMP': '18',
        'ATT': '26',
        'YDS': '239',
        'CMP%': '69.2',
        'AVG': '9.2',
        'TD': '1',
        'INT': '2',
        'LNG': '42',
        'SACK': '1',
        'RTG': '78.9',
        'QBR': '62.3',
        'Result': 'W36-35',
        'OPP': 'vsKC'
    }, {
        'CMP': '19',
        'ATT': '30',
        'YDS': '235',
        'CMP%': '63.3',
        'AVG': '7.8',
        'TD': '1',
        'INT': '0',
        'LNG': '49',
        'SACK': '3',
        'RTG': '98.6',
        'QBR': '57.4',
        'Result': 'L33-27 OT',
        'OPP': '@LV'
    }]
}


class TestsStatsModule:
    """_summary_
    """

    # def test_remove_outliers(self):
    #     """_summary_
    #     """
    #     test_data = [
    #         np.array([-3, 19, 35, 56, 63, 65, 127]),
    #         np.array([120, 144, 174, 210, 213, 218, 318]),
    #         np.array([3, 8, 12, 14, 21, 21, 24])
    #     ]

    #     #values = np.array([int(stat[stat_key]) for stat in stat_section])
    #     for values in test_data:
    #         values.sort()
    #         print("\n\n" + str(values))
    #         if len(values) <= 1:
    #             return values
    #         new_list = []
    #         mean = np.mean(values)
    #         std = np.std(values)
    #         skew_adjustment = stats.skew(values) * 0.25
    #         print("Skew: " + str(stats.skew(values)))
    #         print(skew_adjustment)
    #         print('\n')
    #         print("Lower bound: " + str(-1.5 + skew_adjustment))
    #         print("Upper bound: " + str(1.5 + skew_adjustment))
    #         for stat in values:
    #             z = (stat - mean) / std
    #             print(z)
    #             if -1.5 + skew_adjustment < z < 1.5 + skew_adjustment:
    #                 new_list.append(stat)
    #             else:
    #                 print("Removing outlier stats: " + str(stat))

    # def test_2021_game_year(self):
    #     #https://www.espn.com/nfl/player/gamelog/_/id/4241479/type/nfl/year/2021
    #     #https://www.espn.com/nfl/player/gamelog/_/id/4241479/tua-tagovailoa

    #     espn_game_log_regex = re.compile(r"^(.*?/id/[\d]+/).*?$")
    #     game_year_uri = "type/nfl/year/2021"

    #     print(
    #         espn_game_log_regex.match(
    #             "https://www.espn.com/nfl/player/gamelog/_/id/4241479/tua-tagovailoa"
    #         ).group(1) + "type/nfl/year/2021")

    def test_calculate_weighted_mean(self):
        """_summary_
        """
        # 'W23-7'
        print("Running test")
        SCORE_REGEX = re.compile(r"^[WL]{1}(\d+)[\-]{1}(\d+).*?$")
        stat_key = 'YDS'
        last_year_weight = 85
        this_years_weight = 100
        blow_game_weight = 70
        last_year_yds = list()
        this_years_yds = list()
        blow_out_game_yds = list()
        normal_mean = list()
        total = 0
        for game_log in game_logs['2021']:
            # print("2021: " + str(game_log))
            score_match = SCORE_REGEX.match(game_log['Result'])
            diff = abs(int(score_match.group(1)) - int(score_match.group(2)))
            print(diff)
            if diff > 20:
                print("Blow out game")
                blow_out_game_yds.append(float(game_log[stat_key]))
                normal_mean.append(float(game_log[stat_key]))
            else:
                last_year_yds.append(float(game_log[stat_key]))
                normal_mean.append(float(game_log[stat_key]))
        for game_log in game_logs['2022']:
            # print("2022: " + str(game_log))
            score_match = SCORE_REGEX.match(game_log['Result'])
            diff = abs(int(score_match.group(1)) - int(score_match.group(2)))
            print(diff)
            if diff > 20:
                print("Blow out game")
                blow_out_game_yds.append(float(game_log[stat_key]))
                normal_mean.append(float(game_log[stat_key]))
            else:
                this_years_yds.append(float(game_log[stat_key]))
                normal_mean.append(float(game_log[stat_key]))

        weighted_this_year = 100 * statistics.mean(this_years_yds)
        weighted_blow_out = 70 * statistics.mean(blow_out_game_yds)
        weighted_last_year = 85 * statistics.mean(last_year_yds)

        averge = (weighted_blow_out + weighted_last_year +
                  weighted_this_year) / (100 + 70 + 85)
        print(averge)
        print(statistics.mean(normal_mean))