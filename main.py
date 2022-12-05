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
    "Rush Yds": stats.get_rush_ats_prob,
    "Rec Yds": stats.get_rec_ats_prob,
    "Intercepts": stats.get_inter_ats_prob
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
        'team': [],
        '20+': [],
        '40+': [],
        '60+': [],
        '80+': [],
        'over': []
    }
    if fetch_new_gls:
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

    game_dict = {
        'id': [],
        'prop': [],
        'odds': [],
        'team': [],
        '20+': [],
        '40+': [],
        '60+': [],
        '80+': [],
        'over': []
    }

    df_dict = data_f.to_dict(orient='records')
    rows = len(data_f.axes[0])
    cols = len(data_f.axes[1])
    fig, ax = plt.subplots(figsize=(8, 6))

    ax.set_ylim(-1, rows + 1)
    ax.set_xlim(0, cols + .5)
    for row in range(rows):
        d = df_dict[row]
        # Add data to graph
        ax.text(x=-1, y=row, s=d['id'], va='center', ha='left')
        ax.text(x=1.2, y=row, s=d['prop'], va='center', ha='left')
        ax.text(x=2.5, y=row, s=d['odds'], va='center', ha='left')
        ax.text(x=4.4, y=row, s=d['team'], va='center', ha='left')
        ax.text(x=5.5, y=row, s=d['20+'], va='center', ha='left')
        ax.text(x=6.5, y=row, s=d['40+'], va='center', ha='left')
        ax.text(x=7.5, y=row, s=d['60+'], va='center', ha='left')
        ax.text(x=8.5, y=row, s=d['80+'], va='center', ha='left')
        ax.text(x=9.5, y=row, s=d['over'], va='center', ha='left')

    # Column Title
    ax.text(-1, rows, 'Player', weight='bold', ha='left')
    ax.text(1.2, rows, 'Prop', weight='bold', ha='left')
    ax.text(2.5, rows, 'Odds', weight='bold', ha='left')
    ax.text(4.4, rows, 'Team', weight='bold', ha='left')
    ax.text(5.5, rows, '20+', weight='bold', ha='left')
    ax.text(6.5, rows, '40+', weight='bold', ha='left')
    ax.text(7.5, rows, '60+', weight='bold', ha='left')
    ax.text(8.5, rows, '80+', weight='bold', ha='left')
    ax.text(9.4, rows, 'Over %', weight='bold', ha='left')
    # Creates lines
    for row in range(rows):
        ax.plot([-0.2, cols + .7], [row - 1.5, row - 1.5],
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
    ax.plot([-.5, cols + 0.7], [row + 0.6, row + 0.6], lw='.5', c='black')

    ax.axis('off')
    ax.set_title(game, loc='left', fontsize=18, weight='bold')
    return fig


def _adjust_name_for_chart(name):
    split = name.split("-")
    new_name = split[0].capitalize()[0:1] + ". " + split[1].capitalize()
    return new_name


def process_prop(lines, table, game, spread, total, team_pos, db):
    r"""
      Processes a prop line from prop list gets opponent and
      projection
    """
    for line in lines:
        fields = [field.strip() for field in line.split(',')]
        prop, team, odds = fields[2], fields[1], fields[3]
        if 4 < len(fields):
            pos_rank = fields[4]

        player_name = scraper.convert_player_name_to_espn(
            line.split(",")[0].strip())
        opp = [x.strip() for x in game.split("@")]
        opp.remove(team)
        opp = opp[0]

        if prop in FUNC_FOR_PROP:
            probs = FUNC_FOR_PROP.get(prop)(player_name, opp, team, spread,
                                            total, float(odds.split()[0][1:]),
                                            pos_rank, db)
            if probs == None:
                continue

            table.get('id').append(_adjust_name_for_chart(player_name))
            table.get('prop').append(prop)
            table.get('odds').append(odds)
            table.get('team').append(team)
            table.get('20+').append(probs.get('20+'))
            table.get('40+').append(probs.get('40+'))
            table.get('60+').append(probs.get('60+'))
            table.get('80+').append(probs.get('80+'))
            table.get('over').append(probs.get('over'))


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
conn = sqllite_utils.get_conn()
results_per = []
# for row in sqllite_utils.get_player_stats_sec("jalen-hurts", 'PHI',
#                                               'Passing'):
#     print(f"{row} \n")
# PROP_FILE_TS = "./props/" + START_TIME + "-props.txt"
# prop_file = open(PROP_FILE_TS, 'w', encoding='UTF-8')
# create_prop_file(prop_file, 0, "Sun 12/4")
# prop_file.close()

prop_file = open("./props/" + "1670034167-props.txt", 'r', encoding='UTF-8')
create_report(prop_file, None, False, conn)
prop_file.close()

# prop_file = open("test_props/combined-1.txt", 'r', encoding='UTF-8')
# results_per.append(create_report(prop_file, None, True, conn))
# prop_file.close()

# prop_file = open("test_props/combined-2.txt", 'r', encoding='UTF-8')
# results_per.append(create_report(prop_file, None, True, conn))
# prop_file.close()

# prop_file = open("test_props/combined-3.txt", 'r', encoding='UTF-8')
# results_per.append(create_report(prop_file, None, True, conn))
# prop_file.close()

# prop_file = open("test_props/combined-4.txt", 'r', encoding='UTF-8')
# results_per.append(create_report(prop_file, None, True, conn))
# prop_file.close()

# print(results_per)
# if len(results_per) > 1:
#     print(f"Total correct: {np.mean(results_per)}")
# else:
#     print(f"Total correct: {results_per}")

# # finally:

#     prop_file.close()
