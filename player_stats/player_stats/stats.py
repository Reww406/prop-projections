from tracemalloc import Statistic
import statistics
import scraper

DEFENSE_PAGE = scraper.get_team_def_stats_table()
TOP_PASS_D = scraper.get_top_passing_d(DEFENSE_PAGE, 5)
TOP_RUSHING_D = scraper.get_top_rushing_d(DEFENSE_PAGE, 5)
WORST_RUSHING_D = scraper.get_worst_rushing_d(DEFENSE_PAGE, 5)
WORST_PASS_D = scraper.get_worst_passing_d(DEFENSE_PAGE, 5)

RUSH_D_WEIGHT = 2
PASS_D_WEIGHT = 3
REC_D_WEIGHT = 0.5
SEASON_KEY = "2022 Regular Season"
RUSHING_KEY = "Rushing"
RECEIVING_KEY = "Receiving"
FUMBLES_KEY = "Fumbles"
PASSING_KEY = "Passing"

def remove_outliers(stat_key, stat_section):
  values = list()
  for stats in stat_section: values.append(int(stats[stat_key]))
  if len(values) <= 1:
    return values
  new_list = list()
  mean = statistics.mean(values)
  sigma = statistics.stdev(values)
  max = mean + 1.25 * sigma
  min = mean - 1.25 * sigma
  for stat in values:
    if stat < max and stat > min:
      new_list.append(stat)
    else:
      print("Removing: " + str(stat))
  return new_list
  
def prop_string(prop, projection) -> str():
  return prop + ", Proj: " + str(projection) + '\n'

def add_rushing_weight_to_proj(opp, proj):
  if opp in TOP_RUSHING_D:
    print("Playing good D")
    return proj - RUSH_D_WEIGHT
  elif opp in WORST_RUSHING_D:
    print("Playing worst D")
    return proj + RUSH_D_WEIGHT
  else:
    return proj

def add_pass_weight_to_proj(opp, proj):
  if opp in TOP_PASS_D:
    print("Playing good D")
    return proj - PASS_D_WEIGHT
  elif opp in WORST_PASS_D:
    print("Playing worst D")
    return proj + PASS_D_WEIGHT
  else:
    return proj

def add_rec_weight_to_proj(opp, proj):
  if opp in TOP_PASS_D:
    print("Playing good D")
    return proj - REC_D_WEIGHT
  elif opp in WORST_PASS_D:
    print("Playing worst D")
    return proj + REC_D_WEIGHT
  else:
    return proj
  
def calc_rush_att_proj(prop, gamelogs, opp):
  rush_stats = get_stats(gamelogs, RUSHING_KEY)
  proj = statistics.mean(remove_outliers('ATT', rush_stats))
  return prop_string(prop,add_rushing_weight_to_proj(opp, proj))
  
def calc_pass_att_proj(prop, gamelogs, opp):
  pass_stats = get_stats(gamelogs, PASSING_KEY)
  proj = statistics.mean(remove_outliers('ATT', pass_stats))
  return prop_string(prop,add_pass_weight_to_proj(opp, proj))

def calc_pass_comp_proj(prop, gamelogs, opp):
  pass_stats = get_stats(gamelogs, PASSING_KEY)
  proj =  statistics.mean(remove_outliers('CMP', pass_stats))
  return prop_string(prop,add_pass_weight_to_proj(opp, proj))

def calc_rec_proj(prop, gamelogs, opp):
  rec_stats = get_stats(gamelogs, RECEIVING_KEY)
  proj = statistics.mean(remove_outliers('REC', rec_stats))
  return prop_string(prop,add_rec_weight_to_proj(opp, proj))

def get_stats(gamelogs, stat_key):
  stats = list()
  for game in gamelogs:
    stat_section = game[stat_key]
    stat_section["Result"] = game[SEASON_KEY]["Result"]
    stat_section["OPP"] = game[SEASON_KEY]['OPP']
    stats.append(stat_section)
  return stats