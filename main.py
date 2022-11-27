"""
  Main python file that kicks off script processes file and creates output.
"""

import re
import json
import time
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.backends.backend_pdf
import numpy as np
import sklearn.metrics as metrics

from player_stats import scraper, sqllite_utils
from player_stats import stats
from player_stats import constants as const

GAME_REGEX = re.compile(r"^\w+\s*@\s*\w+$", re.IGNORECASE)
SPREAD_REGEX = re.compile(r"^Spread[:]\s(.*?)$", re.IGNORECASE)
TOTAL_REGEX = re.compile(r"^Total[:]\s(.*?)$", re.IGNORECASE)
DATE_REGEX = re.compile(r"^Date[:]\s(.*?)$", re.IGNORECASE)
HURT_PLAYER_RE = re.compile(r"^(\w{2,3})\sstarting\s(\w{1,2}).*?$",
                            re.IGNORECASE)

# Maps function to stats function for calculating projection
FUNC_FOR_PROP = {
    "Rush Yds": stats.calc_rush_yds_proj,
    "Rec Yds": stats.calc_rec_yds_proj
}

OPP_REGEX = re.compile(r"^(@|vs)(\w+)$")

START_TIME = str(int(time.time()))


# get unique players
def get_team_players(prop_lines):
    r"""
        :param lines are lines from the 'prop' file generated
        Gets unique players per team return dict
        team : player name
    """
    players = {}
    for line in prop_lines:
        player_name = scraper.convert_player_name_to_espn(line)
        team = line.split(",")[1].strip()
        if team in players:
            players[team] += [player_name]
        else:
            players[team] = [player_name]
    return players


def add_gamelogs(prop_lines, db):
    r"""
        :param prop_lines is lines in prop file generated from DK
        add_gamelogs to database
    """
    team_for_players = get_team_players(prop_lines)
    for team in team_for_players:
        scraper.add_gamelogs_to_db(team, team_for_players.get(team), db)


def create_fig(prop_lines, game, spread, total, date, figs, results_fn,
               fetch_new_gls, result_per, team_pos, db):
    """
    Creates figure from a finished game.
    Args:
        prop_lines (list): prop_lines from file
        game_dict (dict): _description_
        game (str): game title
        spread (str): spread of game
        total (str): total from DK
        date (str): date
        figs (list): list of figures
        results_fn (function): function to process results
    """
    game_dict = {
        'id': [],
        'prop': [],
        'odds': [],
        'projection': [],
        'team': [],
        'over%': []
    }
    if (fetch_new_gls):
        print("Storing new game logs in DB")
        add_gamelogs(prop_lines, db)
    process_prop(prop_lines, game_dict, game, spread, total, team_pos, db)
    if results_fn is not None:
        results_fn(game_dict, game, spread, total, date, result_per, db)
    else:
        figs.append(build_graphic(pd.DataFrame(game_dict), game))


# Pretty much the main function
def create_report(read_file, results_fn, fetch_new_gls, db):
    r"""
      Reads in a file with props listed on each line and then get projection
      and create PDF with muliplte graphics..
    """
    game_date = ""
    current_prop_lines, current_game, current_spread, current_total = [], "", None, 0
    figs = []
    result_per = []
    team_pos = {}
    for line in read_file:
        game_match = GAME_REGEX.match(line)
        total_match = TOTAL_REGEX.match(line)
        spread_match = SPREAD_REGEX.match(line)
        date_match = DATE_REGEX.match(line)
        hurt_pos = HURT_PLAYER_RE.match(line)
        if len(line.strip()) == 0:
            continue
        if bool(hurt_pos):
            if team_pos.get(hurt_pos.group(1)) is None:
                team_pos[hurt_pos.group(1)] = [hurt_pos.group(2)]
            else:
                team_pos[hurt_pos.group(1)].append(hurt_pos.group(2))
            continue
        if bool(date_match):
            game_date = date_match.group(1)
            continue
        if bool(total_match):
            current_total = float(total_match.group(1).strip())
            continue
        if bool(spread_match):
            current_spread = json.loads(
                spread_match.group(1).replace("'", '"').strip())
            continue
        if bool(game_match):
            # print(f"Found game: {game_match.group(0)}")
            if len(current_game) > 0 and current_game != game_match.group(0):
                # Not the first game found..
                create_fig(current_prop_lines, current_game, current_spread,
                           current_total, game_date, figs, results_fn,
                           fetch_new_gls, result_per, team_pos, db)
                current_prop_lines = []
                team_pos = {}
                current_game = game_match.group(0).strip()
            elif current_game != game_match.group(0):
                # First game in file
                current_game = game_match.group(0)
        else:
            # if nothing else then prop line..
            if line.split(",")[1].strip() == 'TNF':
                # print("Skipping TNF")
                continue
            current_prop_lines.append(line)
    # print(team_pos)
    create_fig(current_prop_lines, current_game, current_spread, current_total,
               game_date, figs, results_fn, fetch_new_gls, result_per,
               team_pos, db)
    team_pos = {}
    if results_fn is None:
        pdf = matplotlib.backends.backend_pdf.PdfPages("./reports/" +
                                                       START_TIME +
                                                       '-report.pdf')
        for fig in figs:
            pdf.savefig(fig)
        pdf.close()
    if len(result_per) > 0:
        # print(f"Correct percentage: {np.mean(result_per)}")
        return np.mean(result_per)
    return 0


# TODO game_dict needs team for this function to work...
def create_results(game_dict, current_game, spread, total, date, result_per,
                   db):
    """
        Checks how the projections went per player per prop
    """
    teams = current_game.split('@')
    file_name = './results/' + spread.get(teams[0].strip(
    ))[1:] + "-" + teams[0].strip() + "-" + teams[1].strip() + "-v3.txt"

    results_file = open(file_name, 'w', encoding='UTF-8')
    results_file.write("Game: " + str(current_game) + "\n")
    results_file.write("Spread: " + str(spread) + "\n")
    results_file.write("Total: " + str(total) + "\n")
    correct = 0.0
    total = 0.0
    for i in range(len(game_dict.get("id"))):
        player_name = game_dict.get('id')[i]
        prop = game_dict.get('prop')[i]
        most_recent_game = _get_game_stats(player_name,
                                           game_dict.get('team')[i], date,
                                           prop, db)
        if most_recent_game is None:
            continue
        opp = OPP_REGEX.match(most_recent_game['opp']).group(2)
        teams = [team.strip() for team in current_game.split('@')]
        teams.remove(opp)
        actual_stat = get_stat_from_db_row(prop, most_recent_game)
        odds = game_dict.get('odds')[i].split()[0]
        odds_num = float(odds[1:])
        proj = float(game_dict.get('projection')[i])
        hit = "Wrong"
        if actual_stat != -1:
            if proj > odds_num and actual_stat > odds_num:
                hit = "Hit Over"
            elif proj < odds_num and actual_stat > odds_num:
                hit = "Under Projected"
            elif proj > odds_num and actual_stat < odds_num:
                hit = "Over Projected"
            elif proj < odds_num and actual_stat < odds_num:
                hit = "Hit Under"
        if hit.find("Projected") == -1:
            correct += 1.0
        total += 1.0

        results_file.write(player_name + ", " + teams[0] + ", " + str(prop) +
                           ", " + str(odds) + ", P:" + str(proj) + ", A:" +
                           str(actual_stat) + ", " + str(hit) + '\n')
    if total > 0:
        percentage = (float(correct / total)) * 100
        result_per.append(percentage)
        results_file.write("\n\n Correct: " + str(percentage) + "%")
    results_file.close()


def calculate_correct_per(game_dict, current_game, spread, total, date,
                          result_per, db):
    """
        Checks how the projections went per player per prop
    """
    teams = current_game.split('@')

    correct = 0.0
    total = 0.0
    for i in range(len(game_dict.get("id"))):
        player_name = game_dict.get('id')[i]
        prop = game_dict.get('prop')[i]
        most_recent_game = _get_game_stats(player_name,
                                           game_dict.get('team')[i], date,
                                           prop, db)
        if most_recent_game is None:
            continue
        opp = OPP_REGEX.match(most_recent_game['opp']).group(2)
        teams = [team.strip() for team in current_game.split('@')]
        teams.remove(opp)
        actual_stat = get_stat_from_db_row(prop, most_recent_game)
        odds = game_dict.get('odds')[i].split()[0]
        proj = float(game_dict.get('projection')[i])
        odds_num = float(odds[1:])
        hit = "Wrong"
        if actual_stat != -1:
            if proj > odds_num and actual_stat > odds_num:
                hit = "Hit Over"
            elif proj < odds_num and actual_stat > odds_num:
                hit = "Under Projected"
            elif proj > odds_num and actual_stat < odds_num:
                hit = "Over Projected"
            elif proj < odds_num and actual_stat < odds_num:
                hit = "Hit Under"
        if hit.find("Projected") == -1:
            correct += 1.0
        total += 1.0

    if total > 0:
        percentage = (float(correct / total)) * 100
        result_per.append(percentage)


def calculate_error_per(game_dict, current_game, spread, total, date,
                        result_per, db):
    """
        Checks how the projections went per player per prop
    """
    y_true = []
    y_pred = []
    for i in range(len(game_dict.get("id"))):
        player_name = game_dict.get('id')[i]
        prop = game_dict.get('prop')[i]
        most_recent_game = _get_game_stats(player_name,
                                           game_dict.get('team')[i], date,
                                           prop, db)
        if most_recent_game is None:
            continue
        actual_stat = get_stat_from_db_row(prop, most_recent_game)
        proj = float(game_dict.get('projection')[i])
        if actual_stat > 0:
            y_true.append(actual_stat)
            y_pred.append(proj)
    result_per.append(
        metrics.mean_absolute_percentage_error(y_true=y_true, y_pred=y_pred))


def _get_game_stats(player_name, team_initial, game_date, prop, db):
    """
        Gets the most recent gamelog for player
    """
    player_name = scraper.convert_player_name_to_espn(player_name)
    return sqllite_utils.get_game_stats(player_name, team_initial, game_date,
                                        get_stat_db(prop), db)


# TODO Get from database row.. same as dict
def get_stat_from_db_row(prop, row):
    """
        Gets actual stat from most recent game
    """
    if row is None:
        return '-1'
    if prop.lower() == 'rush attempts':
        return float(row['att'])
    if prop.lower() == 'receptions':
        return float(row['rec'])
    if prop.lower() == 'rec yds':
        return float(row['yds'])
    if prop.lower() == 'rush yds':
        return float(row['yds'])
    if prop.lower() == 'pass attempts':
        return float(row['att'])
    if prop.lower() == 'pass completions':
        return float(row['cmp'])
    if prop.lower() == 'pass yds':
        return float(row['yds'])
    return 0.0


def get_stat_db(prop):
    """
        Gets actual stat from most recent game
    """
    if prop.lower() == 'rush attempts' or prop.lower() == 'rush yds':
        return const.SECTION_FOR_TABLE.get(const.RUSHING_KEY)
    if prop.lower() == 'receptions' or prop.lower() == 'rec yds':
        return const.SECTION_FOR_TABLE.get(const.RECEIVING_KEY)
    if prop.lower() == 'pass attempts' or prop.lower(
    ) == 'pass completions' or prop.lower() == 'pass yds':
        return const.SECTION_FOR_TABLE.get(const.PASSING_KEY)


def build_graphic(data_f, game):
    """
        Takes Pandas data frame and builds a table from it
    """

    df_dict = data_f.to_dict(orient='records')
    rows = len(data_f.axes[0])
    cols = len(data_f.axes[1])
    fig, ax = plt.subplots(figsize=(8, 6))

    ax.set_ylim(-1, rows + 1)
    ax.set_xlim(0, cols + .5)
    for row in range(rows):
        d = df_dict[row]
        # Add data to graph
        ax.text(x=.3, y=row, s=d['id'], va='center', ha='left')
        ax.text(x=1.9, y=row, s=d['team'], va='center', ha='left')
        ax.text(x=2.6, y=row, s=d['prop'], va='center', ha='left')
        ax.text(x=3.5, y=row, s=d['odds'], va='center', ha='left')
        ax.text(x=4.8, y=row, s=d['over%'], va='center', ha='left')
        ax.text(x=6.4, y=row, s=d['projection'], va='center', ha='right')

    # Column Title
    ax.text(.3, rows, 'Player', weight='bold', ha='left')
    ax.text(2.1, rows, 'Team', weight='bold', ha='center')
    ax.text(2.6, rows, 'Prop', weight='bold', ha='left')
    ax.text(3.5, rows, 'Odds', weight='bold', ha='left')
    ax.text(5.0, rows, 'Over%', weight='bold', ha='center')
    ax.text(6.4, rows, 'Projection', weight='bold', ha='right')
    # Creates lines
    for row in range(rows):
        ax.plot([0, cols + .7], [row - .5, row - .5],
                ls=':',
                lw='.5',
                c='grey')
    # rect = patches.Rectangle(
    #     (1.5, -.5),  # bottom left starting position (x,y)
    #     .65,  # width
    #     10,  # height
    #     ec='none',
    #     fc='grey',
    #     alpha=.2,
    #     zorder=-1)
    # line under title
    ax.plot([0, cols + 0.7], [row + 0.6, row + 0.6], lw='.5', c='black')

    ax.axis('off')
    ax.set_title(game, loc='left', fontsize=18, weight='bold')
    return fig


def adjust_name_for_chart(name):
    split = name.split("-")
    new_name = split[0].capitalize() + " " + split[1].capitalize()
    return new_name


#  Jerick McKinnon, KC, Rec Yds, o13.5 −120,
def _get_stat_and_section(prop):
    if prop.strip() == 'Rec Yds':
        return [const.RECEIVING_KEY, 'yds']
    elif prop.strip() == 'Rush Yds':
        return [const.RUSHING_KEY, 'yds']


# TODO fix for SQL
def process_prop(lines, table, game, spread, total, team_pos, db):
    r"""
      Processes a prop line from prop list gets opponent and
      projection
    """
    for line in lines:
        fields = [field.strip() for field in line.split(',')]
        prop, team, odds = fields[2], fields[1], fields[3]
        player_name = scraper.convert_player_name_to_espn(
            line.split(",")[0].strip())
        opp = [x.strip() for x in game.split("@")]
        # TODO FAILING ON TNF
        opp.remove(team)
        opp = opp[0]
        # print(f"Calculating proj for: {player_name}")
        if prop in FUNC_FOR_PROP:

            proj = FUNC_FOR_PROP.get(prop)(player_name, opp, team, spread,
                                           total, team_pos, db)
            if proj is not None:
                table.get('id').append(adjust_name_for_chart(player_name))
                table.get('prop').append(prop)
                table.get('projection').append(proj)
                table.get('odds').append(odds)
                table.get('team').append(team)
                odds_num = float(odds.split()[0][1:])
                sec_and_stat = _get_stat_and_section(prop)
                table.get('over%').append(
                    stats.calculate_ats(player_name, team, sec_and_stat[0],
                                        sec_and_stat[1], odds_num, db))
            else:
                # print("Couldn't get projection..")
                pass
        else:
            print(f"No func for prop: {prop}")


def _create_prop_str(prop):
    """
        creates line for prop
    """
    prop_line = ""
    for sec in prop:
        prop_line += sec + ", "
    return prop_line.strip()[0:len(prop_line) - 1] + "\n"


def create_prop_file(file, dk_table_num, date_of_games):
    """_
        Which table to scrape.. dk_table_num relates to which
        table of games.. monday tuesday etc..
    """
    game_info = scraper.get_game_info_from_dk(dk_table_num)
    file.write("Date: " + date_of_games + "\n\n")
    for page in game_info:
        props, spread, total = page[0], page[1], page[2]
        file.write(next(iter(props)) + "\n")
        for hurt_player in scraper.get_hurt_players(
                next(iter(props)).split('@')):
            file.write(f"{hurt_player}\n")
        file.write("Spread: " + str(spread.get('Spread')) + "\n")
        file.write("Total: " + total.get('Total') + "\n\n")
        write_props(props, file)


def write_props(props, file):
    """
        Parses the two prop pages from DK for a game
    """
    parsed_props = scraper.parse_dk_prop_pages(props)

    for prop in parsed_props:
        file.write(_create_prop_str(prop))
    file.write("\n\n")

    # When getting players links get there depth chart pos and actual pos
    # fix names with - and st.


# try:
# results_per = []
# for row in sqllite_utils.get_player_stats_sec("jalen-hurts", 'PHI',
#                                               'Passing'):
#     print(f"{row} \n")
# PROP_FILE_TS = "./props/" + START_TIME + "-props.txt"
# prop_file = open(PROP_FILE_TS, 'w', encoding='UTF-8')
# create_prop_file(prop_file, 0, "Thu 11/24")
# prop_file.close()

# prop_file = open(PROP_FILE_TS, 'r', encoding='UTF-8')
# create_report(prop_file, None, False)
# prop_file.close()

# prop_file = open("props/first-week-v2.txt", 'r', encoding='UTF-8')
# results_per.append(create_report(prop_file, calculate_error_per, False))
# prop_file.close()

# prop_file = open("props/second-week-v2.txt", 'r', encoding='UTF-8')
# results_per.append(create_report(prop_file, calculate_error_per, False))
# prop_file.close()

# prop_file = open("props/third-week-v2.txt", 'r', encoding='UTF-8')
# results_per.append(create_report(prop_file, calculate_error_per, False))
# prop_file.close()

# prop_file = open("props/fourth-week-v2.txt", 'r', encoding='UTF-8')
# results_per.append(create_report(prop_file, calculate_error_per, False))
# prop_file.close()

# print(results_per)
# if len(results_per) > 1:
#     print(f"Total correct: {np.mean(results_per)}")
# else:
#     print(f"Total correct: {results_per}")

# finally:
# scraper.driver_quit()
#     prop_file.close()
