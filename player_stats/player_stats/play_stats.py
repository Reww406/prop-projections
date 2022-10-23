"""
  Main python file that kicks off script processes file and creates output.
"""

import re
import time
import scraper
import stats

game_regex = re.compile(r"^game:\s(.*?)$", re.IGNORECASE)
pass_attempt_prop = re.compile(r".*?\s(?:pass|passing)\s(atts|attempts).*?",
                               re.IGNORECASE)
rush_attempt_prop = re.compile(r".*?\s(?:rush|rushing)\s(atts|attempts).*?",
                               re.IGNORECASE)
receptions_prop = re.compile(r".*?\s(?:rec|receptions).*?", re.IGNORECASE)
completions_prop = re.compile(r"^.*?(?:cmp|completions).*?$", re.IGNORECASE)

# receiving_prop = re.compile(".*?\s(?:rec|receiving)|(?:receptions)\s.*?", re.IGNORECASE)
# yards_prop = re.compile("^.*?(?:yards|yds).*?$", re.IGNORECASE)
# attempts_prop = re.compile("^.*?(?:attempts|atts).*?$", re.IGNORECASE)
# completions_prop = re.compile("^.*?(?:cmp|completions).*?$", re.IGNORECASE)
# tds_prop = re.compile("^.*?(?:tds|touchdowns).*?$", re.IGNORECASE)
# int_prop = re.compile("^.*?(?:int|interceptions).*?$", re.IGNORECASE)

TEAM_DEF_STATS = scraper.get_team_def_stats_table()


# get unique players
def get_team_players(lines):
    r"""
      Gets unique players per team return dict
      team : player name
    """
    players = {}
    for line in lines:
        player_name = line.split(",")[0].strip()
        team = line.split(",")[1].strip()
        if team in players.keys():
            players[team] += [player_name]
        else:
            players[team] = [player_name]
    return players


#player name position, team, prop bet
def get_gamelogs(prop_lines):
    r"""
      Call Scraper to get player game logs for team..
      returns team : gamelogs
    """
    players = get_team_players(prop_lines)
    team_gamelog = {}
    for team in players.keys():
        team_gamelog[team] = scraper.get_player_gamelog_per_team(
            team, players.get(team))
    return team_gamelog


def process_file(file, new_file):
    r"""
      Process prop file hand generated now, but will be
      created from draft kings
    """
    current_prop_lines = []
    current_game = ""
    for line in file:
        game_match = game_regex.match(line)
        if len(line.strip()) == 0:
            continue
        if line[0] == '#':
            new_file.write(line.strip() + " \n")
            continue
        if bool(game_match):
            if len(current_game) > 0 and current_game != game_match.group(1):
                # new game section, process lines and reset current ones
                gamelogs = get_gamelogs(current_prop_lines)
                process_prop(current_prop_lines, gamelogs, new_file,
                             current_game)
                current_prop_lines = []
                new_file.write("\n\n" + game_match.group(1).strip() + "\n\n")
                current_game = game_match.group(1).strip()
            elif current_game != game_match.group(1):
                # First game in file
                new_file.write(game_match.group(1).strip() + " \n\n")
                current_game = game_match.group(1)
        else:
            # if nothing else then prop line..
            current_prop_lines.append(line)
    gamelogs = get_gamelogs(current_prop_lines)
    process_prop(current_prop_lines, gamelogs, new_file, current_game)


def process_prop(lines, gamelogs, new_file, game):
    r"""
      Processes a prop line from prop list gets opponent and
      projection
    """
    for line in lines:
        prop = line.split(',')[2].strip()
        team = line.split(',')[1].strip()
        player_name = line.split(",")[0].strip()
        opp = [x.strip() for x in game.split("@")].remove(team)[0]
        if gamelogs is not None:
            print("Calculateing Proj for: " + player_name)
            if gamelogs[team].get(player_name) is None:
                new_file.write(player_name + ", " + prop +
                               ", no stats found \n")
            elif bool(rush_attempt_prop.match(prop)):
                new_file.write(player_name + ", " + stats.calc_rush_att_proj(
                    prop, gamelogs[team][player_name], opp))
            elif bool(pass_attempt_prop.match(prop)):
                new_file.write(player_name + ", " + stats.calc_pass_att_proj(
                    prop, gamelogs[team][player_name], opp))
            elif bool(completions_prop.match(prop)):
                new_file.write(player_name + ", " + stats.calc_pass_comp_proj(
                    prop, gamelogs[team][player_name], opp))
            elif bool(receptions_prop.match(prop)):
                new_file.write(player_name + ", " + stats.calc_rec_proj(
                    prop, gamelogs[team][player_name], opp))
        else:
            print("No Gamelog found for: " + player_name)


try:
    f = open("filled-out.txt", "r", encoding='UTF-8')
    new_f = open(str(int(time.time())) + "-props.txt", 'a', encoding='UTF-8')
    process_file(f, new_f)
finally:
    f.close()
    new_f.close()
