"""
  Main python file that kicks off script processes file and creates output.
"""

import re
import json
import time
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.backends.backend_pdf

from player_stats import scraper
from player_stats import stats

GAME_REGEX = re.compile(r"^\w+\s*@\s*\w+$", re.IGNORECASE)
SPREAD_REGEX = re.compile(r"^Spread[:]\s(.*?)$", re.IGNORECASE)
TOTAL_REGEX = re.compile(r"^Total[:]\s(.*?)$", re.IGNORECASE)

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
        T. Name
    """
    # TODO Doesn't work for people with st. in there name or jr or a -
    name_split = line.split(",")[0].strip()
    return name_split[0:1].upper() + ". " + name_split.split()[1].capitalize(
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
    team_for_players = get_team_players(prop_lines)
    team_gamelog = {}
    for team in team_for_players:
        player_stats = scraper.get_player_gamelog_per_team(
            team, team_for_players.get(team))
        if player_stats is not None:
            team_gamelog[team] = player_stats
    return team_gamelog


def create_report(read_file):
    r"""
      Reads in a file with props listed on each line and then get projection
      and create PDF with muliplte graphics..
    """

    game_dict = {'id': [], 'prop': [], 'odds': [], 'projection': []}
    current_prop_lines, current_game, current_spread, current_total = [], "", None, 0
    figs = []
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
                # Not the first game found..
                gamelogs = get_gamelogs(current_prop_lines)
                process_prop(current_prop_lines, gamelogs, game_dict,
                             current_game, current_spread, current_total)
                figs.append(
                    build_graphic(pd.DataFrame(game_dict), current_game))
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
            current_prop_lines.append(line)
    gamelogs = get_gamelogs(current_prop_lines)
    process_prop(current_prop_lines, gamelogs, game_dict, current_game,
                 current_spread, current_total)
    figs.append(build_graphic(pd.DataFrame(game_dict), current_game))

    pdf = matplotlib.backends.backend_pdf.PdfPages('10-30-2022-report.pdf')
    for fig in figs:
        pdf.savefig(fig)
    pdf.close()


def build_graphic(data_f, game):
    """_summary_

    Args:
        df (_type_): _description_
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
        player_name = convert_player_name_to_espn(line.split(",")[0].strip())
        opp = [x.strip() for x in game.split("@")]
        opp.remove(team)
        opp = opp[0]
        if gamelogs is not None:
            print("Calculateing Proj for: " + player_name, line)
            if prop in FUNC_FOR_PROP:
                table.get('id').append(player_name)
                table.get('prop').append(prop)
                table.get('projection').append(
                    FUNC_FOR_PROP.get(prop)(gamelogs[team][player_name], opp,
                                            team, spread, total))
                table.get('odds').append(odds)
            else:
                print("No func for prop: " + prop)
        else:
            print("No Gamelog found for: " + player_name)


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
    parsed_props = scraper.process_dk_prop_pages(props)

    for prop in parsed_props:
        file.write(create_prop_str(prop))
    file.write("\n\n")


try:
    PROP_FILE_TS = str(int(time.time()))
    prop_file = open(str(int(time.time())) + "-prop.txt",
                     'w',
                     encoding='UTF-8')
    create_prop_file(prop_file, 0)
    prop_file.close()

    prop_file = open(PROP_FILE_TS + '-prop.txt', 'r', encoding='UTF-8')
    create_report(prop_file)

    prop_file.close()
finally:
    scraper.driver_quit()
    prop_file.close()
