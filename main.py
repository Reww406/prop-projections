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

from player_stats import scraper
from player_stats import stats

GAME_REGEX = re.compile(r"^\w+\s*@\s*\w+$", re.IGNORECASE)
SPREAD_REGEX = re.compile(r"^Spread[:]\s(.*?)$", re.IGNORECASE)
TOTAL_REGEX = re.compile(r"^Total[:]\s(.*?)$", re.IGNORECASE)
DATE_REGEX = re.compile(r"^Date[:]\s(.*?)$", re.IGNORECASE)

# Maps function to stats function for calculating projection
FUNC_FOR_PROP = {
    "Rush Yds": stats.calc_rush_yds_proj,
    "Pass Yds": stats.calc_pass_yds_proj,
    "Pass Completions": stats.calc_pass_comp_proj,
    "Pass Attempts": stats.calc_pass_att_proj,
    "Rec Yds": stats.calc_rec_yds_proj,
    "Receptions": stats.calc_rec_proj,
    "Rush Attempts": stats.calc_rush_att_proj
}

CURR_YEAR = '2022'
CURR_SEASON = '2022 Regular Season'
OPP_REGEX = re.compile(r"^(@|vs)(\w+)$")

START_TIME = str(int(time.time()))
result_per = []


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


# player name position, team, prop bet
def get_gamelogs(prop_lines):
    r"""
        :param prop_lines is lines in prop file generated from DK
        Call Scraper to get player game logs for team..
        returns team : gamelogs
    """
    team_for_players = get_team_players(prop_lines)
    team_gamelog = {}
    for team in team_for_players:
        player_stats = scraper.get_players_gamelogs(team,
                                                    team_for_players.get(team))
        if player_stats is not None:
            team_gamelog[team] = player_stats
    return team_gamelog


def create_fig(prop_lines, game_dict, game, spread, total, date, figs,
               results_fn):
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
    gamelogs = get_gamelogs(prop_lines)
    process_prop(prop_lines, gamelogs, game_dict, game, spread, total)
    figs.append(build_graphic(pd.DataFrame(game_dict), game))
    if results_fn is not None:
        results_fn(game_dict, gamelogs, game, spread, total, date)


# Pretty much the main function
def create_report(read_file, results_fn):
    r"""
      Reads in a file with props listed on each line and then get projection
      and create PDF with muliplte graphics..
    """
    game_date = ""
    game_dict = {'id': [], 'prop': [], 'odds': [], 'projection': []}
    current_prop_lines, current_game, current_spread, current_total = [], "", None, 0
    figs = []
    for line in read_file:
        game_match = GAME_REGEX.match(line)
        total_match = TOTAL_REGEX.match(line)
        spread_match = SPREAD_REGEX.match(line)
        date_match = DATE_REGEX.match(line)
        if len(line.strip()) == 0:
            continue
        if bool(date_match):
            print(f"Found games date: {date_match.group(1)}")
            game_date = date_match.group(1)
            continue
        if bool(total_match):
            print(f"Found total: {total_match.group(1)}")
            current_total = float(total_match.group(1).strip())
            continue
        if bool(spread_match):
            print(f"Found spread: {spread_match.group(1)}")
            current_spread = json.loads(
                spread_match.group(1).replace("'", '"').strip())
            continue
        if bool(game_match):
            print(f"Found game: {game_match.group(0)}")
            if len(current_game) > 0 and current_game != game_match.group(0):
                # Not the first game found..
                create_fig(current_prop_lines, game_dict, current_game,
                           current_spread, current_total, game_date, figs,
                           results_fn)
                game_dict = {
                    'id': [],
                    'prop': [],
                    'odds': [],
                    'projection': []
                }
                current_prop_lines = []
                current_game = game_match.group(0).strip()
            elif current_game != game_match.group(0):
                # First game in file
                current_game = game_match.group(0)
        else:
            # if nothing else then prop line..
            if line.split(",")[1].strip() == 'TNF':
                print("Skipping TNF")
                continue
            current_prop_lines.append(line)
    create_fig(current_prop_lines, game_dict, current_game, current_spread,
               current_total, game_date, figs, results_fn)
    pdf = matplotlib.backends.backend_pdf.PdfPages("./reports/" + START_TIME +
                                                   '-report.pdf')
    for fig in figs:
        pdf.savefig(fig)
    pdf.close()


def create_results(game_dict, game_logs, current_game, spread, total, date):
    """
        Checks how the projections went per player per prop
    """
    teams = current_game.split('@')
    results_file = open('./results/results-' + teams[0].strip() + "-" +
                        teams[1].strip() + "-v2.txt",
                        'w',
                        encoding='UTF-8')
    results_file.write("Game: " + str(current_game) + "\n")
    results_file.write("Spread: " + str(spread) + "\n")
    results_file.write("Total: " + str(total) + "\n")
    correct = 0.0
    total = 0.0
    for i in range(len(game_dict.get("id"))):
        player_name = game_dict.get('id')[i]
        most_recent_game = get_most_recent_game(player_name, game_logs, date)
        if most_recent_game is None:
            continue
        opp = OPP_REGEX.match(
            most_recent_game.get(CURR_SEASON).get("OPP")).group(2)
        teams = [team.strip() for team in current_game.split('@')]
        teams.remove(opp)
        prop = game_dict.get('prop')[i]
        actual_stat = get_stat_from_game_log(prop, most_recent_game)
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

        results_file.write(player_name + ", " + teams[0] + ", " + str(prop) +
                           ", " + str(odds) + ", P:" + str(proj) + ", A:" +
                           str(actual_stat) + ", " + str(hit) + '\n')
    if total > 0:
        percentage = (float(correct / total)) * 100
        result_per.append(percentage)
        results_file.write("\n\n Correct: " + str(percentage) + "%")
    results_file.close()


def get_most_recent_game(player_name, game_logs, game_date):
    """
        Gets the most recent gamelog for player
    """
    for team_name in game_logs:
        games = game_logs.get(team_name)
        player_games = games.get(player_name)
        if player_games is not None:
            for game in player_games:
                if game.get(CURR_SEASON) is not None:
                    this_games_date = game.get(CURR_SEASON).get('Date').lower()
                    if this_games_date == game_date.lower():
                        return game

    return None


# TODO Fix this ugliness
def get_stat_from_game_log(prop, game_log):
    """
        Gets actual stat from most recent game
    """
    if game_log is None:
        return '-1'
    if prop.lower() == 'rush attempts':
        return float(game_log.get('Rushing').get('ATT'))
    if prop.lower() == 'receptions':
        return float(game_log.get('Receiving').get('REC'))
    if prop.lower() == 'rec yds':
        return float(game_log.get('Receiving').get('YDS'))
    if prop.lower() == 'rush yds':
        return float(game_log.get('Rushing').get('YDS'))
    if prop.lower() == 'pass attempts':
        return float(game_log.get('Passing').get('ATT'))
    if prop.lower() == 'pass completions':
        return float(game_log.get('Passing').get('CMP'))
    if prop.lower() == 'pass yds':
        return float(game_log.get('Passing').get('YDS'))
    return 0.0


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
        ax.text(x=2.3, y=row, s=d['prop'], va='center', ha='right')
        ax.text(x=3.4, y=row, s=d['odds'], va='center', ha='right')
        ax.text(x=4.3, y=row, s=d['projection'], va='center', ha='right')

    # Column Title
    ax.text(.3, rows, 'Player', weight='bold', ha='left')
    ax.text(2.3, rows, 'Prop', weight='bold', ha='right')
    ax.text(3.4, rows, 'Odds', weight='bold', ha='right')
    ax.text(4.3, rows, 'Projection', weight='bold', ha='right')
    # Creates lines
    for row in range(rows):
        ax.plot([0, cols + 0.7], [row - .5, row - .5],
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


def process_prop(lines, gamelogs, table, game, spread, total):
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
        if gamelogs is not None:
            print(f"Calculating proj for: {player_name}")
            if prop in FUNC_FOR_PROP:
                if gamelogs[team].get(player_name) is None:
                    print(f"{player_name} is not a start.")
                    continue
                table.get('id').append(player_name)
                table.get('prop').append(prop)
                table.get('projection').append(
                    FUNC_FOR_PROP.get(prop)(gamelogs[team][player_name], opp,
                                            team, spread, total))
                table.get('odds').append(odds)
            else:
                print(f"No func for prop: {prop}")
        else:
            print(f"No Gamelog found for: {player_name}")


def create_prop_str(prop):
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
        file.write("Spread: " + str(spread.get('Spread')) + "\n")
        file.write("Total: " + total.get('Total') + "\n\n")
        write_props(props, file)


def write_props(props, file):
    """
        Parses the two prop pages from DK for a game
    """
    parsed_props = scraper.parse_dk_prop_pages(props)

    for prop in parsed_props:
        file.write(create_prop_str(prop))
    file.write("\n\n")


# When getting players links get there depth chart pos and actual pos
# fix names with - and st.
try:
    # PROP_FILE_TS = "./props/" + START_TIME + "-props.txt"
    # prop_file = open(PROP_FILE_TS, 'w', encoding='UTF-8')
    # create_prop_file(prop_file, 1, "Mon 11-7")
    # prop_file.close()

    prop_file = open("./props/second-week.txt", 'r', encoding='UTF-8')
    create_report(prop_file, create_results)
    # create_report(prop_file, None)

    prop_file.close()

    prop_file = open("./props/first-week.txt", 'r', encoding='UTF-8')
    create_report(prop_file, create_results)
    # create_report(prop_file, None)

    prop_file.close()
    print(f"Total result: {np.array(result_per).mean()}")
finally:
    scraper.driver_quit()
    prop_file.close()
