import re
import time
import scraper
import stats

game_regex = re.compile("^game:\s(.*?)$", re.IGNORECASE)
pass_attempt_prop = re.compile(".*?\s(?:pass|passing)\s(atts|attempts).*?", re.IGNORECASE)
rush_attempt_prop = re.compile(".*?\s(?:rush|rushing)\s(atts|attempts).*?", re.IGNORECASE)
receptions_prop = re.compile(".*?\s(?:rec|receptions).*?", re.IGNORECASE)
completions_prop = re.compile("^.*?(?:cmp|completions).*?$", re.IGNORECASE)


# receiving_prop = re.compile(".*?\s(?:rec|receiving)|(?:receptions)\s.*?", re.IGNORECASE)
# yards_prop = re.compile("^.*?(?:yards|yds).*?$", re.IGNORECASE)
# attempts_prop = re.compile("^.*?(?:attempts|atts).*?$", re.IGNORECASE)
# completions_prop = re.compile("^.*?(?:cmp|completions).*?$", re.IGNORECASE)
# tds_prop = re.compile("^.*?(?:tds|touchdowns).*?$", re.IGNORECASE)
# int_prop = re.compile("^.*?(?:int|interceptions).*?$", re.IGNORECASE)

TEAM_DEF_STATS = scraper.get_team_def_stats_table()

# get unique players
def get_team_players(lines):
  players = dict()
  for line in lines:
    player_name = line.split(",")[0]
    player_name = player_name.split()[0].strip() + ' ' + player_name.split()[1].strip()
    team = line.split(",")[1].strip()
    if team in players.keys():
      players[team] += [player_name]
    else:
      players[team] = [player_name]
  return players

#player name position, team, prop bet
def get_gamelogs(prop_lines):
  players = get_team_players(prop_lines)
  team_gamelog = dict()
  for team in players.keys():
    team_gamelog[team] = scraper.get_player_gamelog_per_team(team, players.get(team))
  return team_gamelog
    
    
def process_file(file, new_file) -> dict(): 
  current_prop_lines = list()
  current_game = ""
  for line in file:
    game_match = game_regex.match(line)
    if(len(line.strip()) == 0):
      continue
    elif(line[0] == '#'):
      # add line maybe?
      new_file.write(line.strip() + " \n")
      continue
    elif(bool(game_match)):
      if len(current_game) > 0 and current_game != game_match.group(1):
        # new game section, process lines and rest current ones
        gamelogs = get_gamelogs(current_prop_lines)
        process_prop(current_prop_lines, gamelogs, new_file, current_game)
        current_prop_lines = list()
        new_file.write("\n\n" + game_match.group(1).strip() + "\n\n")
        current_game = game_match.group(1).strip()
      elif current_game != game_match.group(1):
        new_file.write(game_match.group(1).strip() + " \n\n")
        current_game = game_match.group(1)
    else: 
      current_prop_lines.append(line)
  gamelogs = get_gamelogs(current_prop_lines)
  process_prop(current_prop_lines, gamelogs, new_file, current_game)


def process_prop(lines, gamelogs, new_file, game):
  for line in lines:
    prop = line.split(',')[2].strip()
    team = line.split(',')[1].strip()
    player_name = line.split(",")[0].strip()
    player_name = player_name.split()[0].strip() + ' ' + player_name.split()[1].strip()
    opp = [x.strip() for x in game.split("@")]
    opp.remove(team)
    opp = opp[0]
    if gamelogs is not None:
      print("Calculateing Proj for: " + player_name)
      if gamelogs[team].get(player_name) is None :
        new_file.write(player_name + ", " + prop + ", no stats found \n")
      elif bool(rush_attempt_prop.match(prop)):
        new_file.write(player_name + ", " + stats.calc_rush_att_proj(prop, gamelogs[team][player_name], opp))
      elif bool(pass_attempt_prop.match(prop)):
        new_file.write(player_name + ", " + stats.calc_pass_att_proj(prop, gamelogs[team][player_name], opp))
      elif bool(completions_prop.match(prop)):
        new_file.write(player_name + ", " + stats.calc_pass_comp_proj(prop, gamelogs[team][player_name], opp))
      elif bool(receptions_prop.match(prop)):
        new_file.write(player_name + ", " + stats.calc_rec_proj(prop, gamelogs[team][player_name], opp))
    else:
      print("No Gamelog found for: " + player_name)

  
f = open("filled-out.txt", "r")
new_f = open(str(int(time.time())) + "-props.txt", 'a')
process_file(f, new_f)
new_f.close()