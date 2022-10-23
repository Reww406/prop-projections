r"""
  Caclulate projections based on player stats..
"""
import statistics
import scraper

DEFENSE_PAGE = scraper.get_team_def_stats_table()
TOP_PASS_D = scraper.get_top_n_team_stats(DEFENSE_PAGE, 5, "Passing", False)
TOP_RUSHING_D = scraper.get_top_n_team_stats(DEFENSE_PAGE, 5, "Rushing", False)
WORST_RUSHING_D = scraper.get_top_n_team_stats(DEFENSE_PAGE, 5, "Rushing",
                                               True)
WORST_PASS_D = scraper.get_top_n_team_stats(DEFENSE_PAGE, 5, "Rushing", True)

RUSH_D_WEIGHT = 2
PASS_D_WEIGHT = 3
REC_D_WEIGHT = 0.5
SEASON_KEY = "2022 Regular Season"
RUSHING_KEY = "Rushing"
RECEIVING_KEY = "Receiving"
FUMBLES_KEY = "Fumbles"
PASSING_KEY = "Passing"
'''
  Ideas for making projections better
  - Take into account the spread of the game heavey underdogs will pass more if they get
    down by a lot.. heavy favriotes will run more
  - When calculating stats take into account the result blow out games could be removed IF
    the spread is close
  - Take into account the weather
  - High total could increase yards

'''


def remove_outliers(stat_key, stat_section):
    r"""
      Removes values X signma away from the mean.
    """
    values = [int(stat[stat_key]) for stat in stat_section]
    if len(values) <= 1:
        return values
    new_list = []
    mean = statistics.mean(values)
    sigma = statistics.stdev(values)
    top_sigma = mean + 1.5 * sigma
    bottom_sigma = mean - 1.5 * sigma
    for stat in values:
        if bottom_sigma < stat < top_sigma:
            new_list.append(stat)
        else:
            print("Removing stat outside of standard deviation: " + str(stat))
    return new_list


def prop_string(prop, projection) -> str():
    r"""
      Create project string for file
    """
    return prop.strip() + ", Proj: " + str(projection) + '\n'


def add_weight_to_proj(opp, proj, weight, top_d, worse_d):
    r"""
      If oppoonent is in top/worse defense list then add/subtract attempts
    """
    if opp in top_d:
        print("Playing top defense subtracting: " + str(weight) +
              " to proj: " + str(proj))
        return proj - weight
    if opp in worse_d:
        print("Playing worst defense adding: " + str(weight) + " from proj: " +
              str(proj))
        return proj + weight
    return proj


def calc_rush_att_proj(prop, gamelogs, opp):
    r"""
      Calculate rush attempt projection
    """
    rush_stats = get_stats(gamelogs, RUSHING_KEY)
    proj = statistics.mean(remove_outliers('ATT', rush_stats))
    return prop_string(
        prop,
        add_weight_to_proj(opp, proj, RUSH_D_WEIGHT, TOP_RUSHING_D,
                           WORST_RUSHING_D))


def calc_pass_att_proj(prop, gamelogs, opp):
    r"""
      Calculate pass attempt projection
    """
    pass_stats = get_stats(gamelogs, PASSING_KEY)
    proj = statistics.mean(remove_outliers('ATT', pass_stats))
    return prop_string(
        prop,
        add_weight_to_proj(opp, proj, PASS_D_WEIGHT, TOP_PASS_D, WORST_PASS_D))


def calc_pass_comp_proj(prop, gamelogs, opp):
    r"""
      Calculate pass completion projection
    """
    pass_stats = get_stats(gamelogs, PASSING_KEY)
    proj = statistics.mean(remove_outliers('CMP', pass_stats))
    return prop_string(
        prop,
        add_weight_to_proj(opp, proj, PASS_D_WEIGHT, TOP_PASS_D, WORST_PASS_D))


def calc_rec_proj(prop, gamelogs, opp):
    r"""
      Calculate receptions projection
    """
    rec_stats = get_stats(gamelogs, RECEIVING_KEY)
    proj = statistics.mean(remove_outliers('REC', rec_stats))
    return prop_string(
        prop,
        add_weight_to_proj(opp, proj, REC_D_WEIGHT, TOP_PASS_D, WORST_PASS_D))


def get_stats(gamelogs, stat_key):
    r"""
      Get list dictionary of stats from gamelog
    """
    stats = []
    for game in gamelogs:
        stat_section = game[stat_key]
        stat_section["Result"] = game[SEASON_KEY]["Result"]
        stat_section["OPP"] = game[SEASON_KEY]['OPP']
        stats.append(stat_section)
    return stats
