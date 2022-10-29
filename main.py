"""
  Main python file that kicks off script processes file and creates output.
"""

import re
import time
import json
import pandas as pd
import matplotlib as mpl
import matplotlib.patches as patches
from matplotlib import pyplot as plt
from pandas.plotting import table

from numpy import append

from player_stats import scraper
from player_stats import stats

GAME_REGEX = re.compile(r"^\w+\s*@\s*\w+$", re.IGNORECASE)
SPREAD_REGEX = re.compile(r"^Spread[:]\s(.*?)$", re.IGNORECASE)
TOTAL_REGEX = re.compile(r"^Total[:]\s(.*?)$", re.IGNORECASE)

TEAM_DEF_STATS = scraper.get_team_def_stats_table()

FUNC_FOR_PROP = {
    "Rush Yds": stats.calc_rush_yds_proj,
    "Pass Yds": stats.calc_pass_yds_proj,
    "Pass Completions": stats.calc_pass_comp_proj,
    "Pass Attempts": stats.calc_pass_att_proj,
    "Rec Yds": stats.calc_rec_yds_proj,
    "Receptions": stats.calc_rec_proj,
    "Rush Attempts": stats.calc_rush_att_proj
}


def convert_player_name_to_espn(line):
    """
        Convert DK name to ESPN
    """
    name_sec = line.split(",")[0].strip()
    return name_sec[0:1].upper() + ". " + name_sec.split()[1].capitalize(
    ).strip()


# get unique players
def get_team_players(lines):
    r"""
      Gets unique players per team return dict
      team : player name
    """
    players = {}
    for line in lines:
        player_name = convert_player_name_to_espn(line)
        team = line.split(",")[1].strip()
        if team in players:
            players[team] += [player_name]
        else:
            players[team] = [player_name]
    return players


# player name position, team, prop bet
def get_gamelogs(prop_lines):
    r"""
      Call Scraper to get player game logs for team..
      returns team : gamelogs
    """
    players = get_team_players(prop_lines)
    team_gamelog = {}
    for team in players:
        team_gamelog[team] = scraper.get_player_gamelog_per_team(
            team, players.get(team))
    return team_gamelog


def create_df(read_file):
    r"""
      Process prop file hand generated now, but will be
      created from draft kings
    """
    game_dict = {'id': [], 'prop': [], 'odds': [], 'projection': []}
    current_prop_lines, current_game, current_spread, current_total = [], "", None, 0
    for line in read_file:
        game_match = GAME_REGEX.match(line)
        total_match = TOTAL_REGEX.match(line)
        spread_match = SPREAD_REGEX.match(line)
        if len(line.strip()) == 0:
            continue
        if bool(total_match):
            print("Found total: " + total_match.group(1))
            current_total = float(total_match.group(1).strip())
            continue
        if bool(spread_match):
            print("Found spread: " + spread_match.group(1))
            current_spread = json.loads(
                spread_match.group(1).replace("'", '"').strip())
            continue
        if bool(game_match):
            print("Found game: " + game_match.group(0))
            if len(current_game) > 0 and current_game != game_match.group(0):
                # new game section, process lines and reset current ones
                gamelogs = get_gamelogs(current_prop_lines)
                process_prop(current_prop_lines, gamelogs, game_dict,
                             current_game, current_spread, current_total)
                current_prop_lines = []
                current_game = game_match.group(0).strip()
            elif current_game != game_match.group(0):
                # First game in file
                current_game = game_match.group(0)
        else:
            # if nothing else then prop line..
            current_prop_lines.append(line)
    gamelogs = get_gamelogs(current_prop_lines)
    process_prop(current_prop_lines, gamelogs, game_dict, current_game,
                 current_spread, current_total)
    data_f = pd.DataFrame(game_dict)
    rows = len(data_f.axes[0])
    cols = len(data_f.axes[1])
    build_graphic(data_f.to_dict(orient='records'), rows, cols, current_game)


def build_graphic(df_dict, rows, cols, game):
    """_summary_

    Args:
        df (_type_): _description_
    """
    print(df_dict)
    fig, ax = plt.subplots(figsize=(8, 6))

    ax.set_ylim(-1, rows + 1)
    ax.set_xlim(0, cols + .5)
    for row in range(rows):
        d = df_dict[row]
        ax.text(x=.5, y=row, s=d['id'], va='center', ha='left')
        # shots column - this is my "main" column, hence bold text

        # ax.text(x=2.2,
        #         y=row,
        #         s=d['game'],
        #         va='center',
        #         ha='right',
        #         weight='bold')
        # passes column

        ax.text(x=2.5, y=row, s=d['prop'], va='center', ha='right')
        # goals column

        ax.text(x=3.5, y=row, s=d['odds'], va='center', ha='right')
        # assists column

        ax.text(x=4.5, y=row, s=d['projection'], va='center', ha='right')

    ax.text(.5, rows, 'Player', weight='bold', ha='left')
    # ax.text(2.2, rows, 'Game', weight='bold', ha='right')
    ax.text(2.5, rows, 'Prop', weight='bold', ha='right')
    ax.text(3.5, rows, 'Odds', weight='bold', ha='right')
    ax.text(4.5, rows, 'Projection', weight='bold', ha='right')
    for row in range(rows):
        ax.plot([0, cols + 1], [row - .5, row - .5], ls=':', lw='.5', c='grey')
    ax.plot([0, cols + 1], [row + 0.5, row + 0.5], lw='.5', c='black')

    # Add rectangle
    # rect = patches.Rectangle(
    #     (1.5, -.5),  # bottom left starting position (x,y)
    #     .65,  # width
    #     rows,  # height
    #     ec='none',
    #     fc='grey',
    #     alpha=.2,
    #     zorder=-1)
    # ax.add_patch(rect)
    ax.axis('off')
    ax.set_title(game, loc='left', fontsize=18, weight='bold')
    fig.savefig('proj-table.pdf')


#game_dict = {'Game': [], 'Player': [], 'Prop': [], 'Over':[], 'Odds': [], 'Projection': []}
def process_prop(lines, gamelogs, table, game, spread, total):
    r"""
      Processes a prop line from prop list gets opponent and
      projection
    """
    for line in lines:
        fields = [field.strip() for field in line.split(',')]
        prop, team, odds = fields[2], fields[1], fields[3]
        player_name = convert_player_name_to_espn(line.split(",")[0].strip())
        opp = [x.strip() for x in game.split("@")]
        opp.remove(team)
        opp = opp[0]
        if gamelogs is not None:
            print("Calculateing Proj for: " + player_name, line)
            if prop in FUNC_FOR_PROP:
                # table.get('game').append(game)
                table.get('id').append(player_name)
                table.get('prop').append(prop)
                table.get('projection').append(
                    FUNC_FOR_PROP.get(prop)(prop, gamelogs[team][player_name],
                                            opp, team, spread, total))
                table.get('odds').append(odds)
            else:
                print("No func for prop: " + prop)
        else:
            print("No Gamelog found for: " + player_name)


# def process_file(read_file, write_file):
#     r"""
#       Process prop file hand generated now, but will be
#       created from draft kings
#     """
#     current_prop_lines, current_game, current_spread, current_total = [], "", None, 0
#     for line in read_file:
#         game_match = GAME_REGEX.match(line)
#         total_match = TOTAL_REGEX.match(line)
#         spread_match = SPREAD_REGEX.match(line)
#         if len(line.strip()) == 0:
#             continue
#         if line[0] == '#':
#             write_file.write(line.strip() + " \n")
#             continue
#         if bool(total_match):
#             print("Found total: " + total_match.group(1))
#             current_total = float(total_match.group(1).strip())
#             continue
#         if bool(spread_match):
#             print("Found spread: " + spread_match.group(1))
#             current_spread = json.loads(
#                 spread_match.group(1).replace("'", '"').strip())
#             continue
#         if bool(game_match):
#             print("Found game: " + game_match.group(0))
#             if len(current_game) > 0 and current_game != game_match.group(0):
#                 # new game section, process lines and reset current ones
#                 gamelogs = get_gamelogs(current_prop_lines)
#                 process_prop(current_prop_lines, gamelogs, write_file,
#                              current_game, current_spread, current_total)
#                 current_prop_lines = []
#                 write_file.write("\n\n" + game_match.group(0).strip() + "\n\n")
#                 current_game = game_match.group(0).strip()
#             elif current_game != game_match.group(0):
#                 # First game in file
#                 write_file.write(game_match.group(0).strip() + " \n\n")
#                 current_game = game_match.group(0)
#         else:
#             # if nothing else then prop line..
#             current_prop_lines.append(line)
#     gamelogs = get_gamelogs(current_prop_lines)
#     process_prop(current_prop_lines, gamelogs, write_file, current_game,
#                  current_spread, current_total)

# def process_prop(lines, gamelogs, write_file, game, spread, total):
#     r"""
#       Processes a prop line from prop list gets opponent and
#       projection
#     """
#     for line in lines:
#         fields = [field.strip() for field in line.split(',')]
#         prop, team, odds = fields[2], fields[1], fields[3]
#         player_name = convert_player_name_to_espn(line.split(",")[0].strip())
#         opp = [x.strip() for x in game.split("@")]
#         opp.remove(team)
#         opp = opp[0]
#         if gamelogs is not None:
#             print("Calculateing Proj for: " + player_name, line)
#             if prop in FUNC_FOR_PROP:
#                 write_file.write(player_name + ", " + FUNC_FOR_PROP.get(prop)
#                                  (prop, gamelogs[team][player_name], opp, team,
#                                   spread, total) + ", " + odds + "\n")
#             else:
#                 print("No func for prop: " + prop)
#         else:
#             print("No Gamelog found for: " + player_name)


def create_prop_str(prop):
    """
        creates line for prop
    """
    prop_line = ""
    for sec in prop:
        prop_line += sec + ", "
    return prop_line.strip()[0:len(prop_line) - 1] + "\n"


def create_prop_file(file, dk_table_num):
    """_
        Which table to scrape.. dk_table_num relates to which
        table of games.. monday tuesday etc..
    """
    game_info = scraper.get_games_from_dk(dk_table_num)
    props, spread, total = game_info[0], game_info[1], game_info[2]
    file.write(next(iter(props)) + "\n")
    file.write("Spread: " + str(spread.get('Spread')) + "\n")
    file.write("Total: " + total.get('Total') + "\n\n")
    write_props(props, file)


def write_props(props, file):
    """
        Parses the two prop pages from DK for a game
    """
    parsed_props = scraper.process_dk_prop_pages(props)

    for prop in parsed_props:
        file.write(create_prop_str(prop))
    file.write("\n\n")


# PROP_FILE_TS = str(int(time.time()))
# # prop_file = open(PROP_FILE_TS + "-props.txt", 'w', encoding='UTF-8')
# proj_file = open(str(int(time.time())) + "-proj.txt", 'w', encoding='UTF-8')
# # create_prop_file(prop_file, 0)
# # prop_file.close()
# # prop_file = open(PROP_FILE_TS + "-props.txt", 'r', encoding='UTF-8')
# prop_file = open("1666844201-props.txt", 'r', encoding='UTF-8')
# create_df(prop_file)

# prop_file.close()
# proj_file.close()
