from datetime import date
from io import FileIO
from operator import truediv
from os import stat
import time
from typing import OrderedDict
from xmlrpc.client import boolean
from more_itertools import take
import requests
from bs4 import BeautifulSoup, SoupStrainer
from bs4 import Tag
import re
import random

name_regex = re.compile("^.*?/name/(\w+)/(.*?)$", re.IGNORECASE)
player_link = re.compile("^.*/player/.*?\d+/([a-zA-Z]+)-([a-zA-Z]+).*?$")

def add_team_initials(urls):
  team_urls_enriched = dict()
  for url in urls:
    team_initial = name_regex.match(url)
    team_urls_enriched[team_initial.group(1).upper()] = url
  return team_urls_enriched

def create_team_name_to_int(team_urls):
  team_name_to_int = dict()
  for url in team_urls.values():
    match = name_regex.match(url.strip())
    name = ""
    for name_part in match.group(2).split("-"):
      name += name_part.strip().capitalize() + " "
    name = name.strip()
    team_name_to_int[name] = match.group(1).upper()
  return team_name_to_int
  
team_def_url = "https://www.espn.in/nfl/stats/team/_/view/defense/teams/8/table/rushing/sort/rushingYardsPerGame/dir/asc"
team_off_url = "https://www.espn.in/nfl/stats/team/_/teams/8"

team_urls = add_team_initials([
  'https://www.espn.com/nfl/team/stats/_/name/mia/miami-dolphins',
  'https://www.espn.com/nfl/team/stats/_/name/dal/dallas-cowboys',
  'https://www.espn.com/nfl/team/stats/_/name/nyg/new-york-giants',
  'https://www.espn.com/nfl/team/stats/_/name/phi/philadelphia-eagles',
  'https://www.espn.com/nfl/team/stats/_/name/wsh/washington-commanders',
  'https://www.espn.com/nfl/team/stats/_/name/chi/chicago-bears',
  'https://www.espn.com/nfl/team/stats/_/name/det/detroit-lions',
  'https://www.espn.com/nfl/team/stats/_/name/gb/green-bay-packers',
  'https://www.espn.com/nfl/team/stats/_/name/min/minnesota-vikings',
  'https://www.espn.com/nfl/team/stats/_/name/atl/atlanta-falcons',
  'https://www.espn.com/nfl/team/stats/_/name/car/carolina-panthers',
  'https://www.espn.com/nfl/team/stats/_/name/no/new-orleans-saints',
  'https://www.espn.com/nfl/team/stats/_/name/tb/tampa-bay-buccaneers',
  'https://www.espn.com/nfl/team/stats/_/name/ari/arizona-cardinals',
  'https://www.espn.com/nfl/team/stats/_/name/lar/los-angeles-rams',
  'https://www.espn.com/nfl/team/stats/_/name/sf/san-francisco-49ers',
  'https://www.espn.com/nfl/team/stats/_/name/sea/seattle-seahawks',
  'https://www.espn.com/nfl/team/stats/_/name/lac/los-angeles-chargers',
  'https://www.espn.com/nfl/team/stats/_/name/ne/new-england-patriots',
  'https://www.espn.com/nfl/team/stats/_/name/nyj/new-york-jets',
  'https://www.espn.com/nfl/team/stats/_/name/bal/baltimore-ravens',
  'https://www.espn.com/nfl/team/stats/_/name/cin/cincinnati-bengals',
  'https://www.espn.com/nfl/team/stats/_/name/cle/cleveland-browns',
  'https://www.espn.com/nfl/team/stats/_/name/pit/pittsburgh-steelers',
  'https://www.espn.com/nfl/team/stats/_/name/hou/houston-texans',
  'https://www.espn.com/nfl/team/stats/_/name/ind/indianapolis-colts',
  'https://www.espn.com/nfl/team/stats/_/name/jax/jacksonville-jaguars',
  'https://www.espn.com/nfl/team/stats/_/name/ten/tennessee-titans',
  'https://www.espn.com/nfl/team/stats/_/name/den/denver-broncos',
  'https://www.espn.com/nfl/team/stats/_/name/kc/kansas-city-chiefs',
  'https://www.espn.com/nfl/team/stats/_/name/lv/las-vegas-raiders',
  'https://www.espn.com/nfl/team/stats/_/name/buf/buffalo-bills'])

team_name_to_int = create_team_name_to_int(team_urls)

# Create game log links
def get_player_gamelog_links(team_page, player_names: list()) -> dict():
  name_link = dict()
  for link in BeautifulSoup(team_page.text, 'html.parser', parse_only=SoupStrainer('a')):
      if not link.has_attr('href'):
        continue
      match = player_link.match(link['href'])
      if match is not None:
        name = match.group(1).strip()[0:1].upper() + "." + " " + match.group(2).strip().capitalize()
        if name not in player_names:
          continue
        if name not in name_link.keys():
          link = match.group(0)
          stats_link = link[:link.index('_') - 1] + "/gamelog" + link[link.index('_') - 1:]
          name_link[name] = stats_link
  return name_link

#
# Create Game Log Secion
#

# Creates 2D array of table
def parse_gamelog_tbody(tbody):
  stats = list()
  rows = tbody.findChildren('tr')
  for row in rows:
    row_data = list()
    for td in row.findChildren('td'):
      row_data.append(td.text)
    stats.append(row_data)
  return stats

def pare_team_stats_tbody(team_tb, stats_tb):
  stats = list()
  team_name_rows = team_tb.findChildren('tr')
  team_stat_rows = stats_tb.findChildren('tr')
  for team_name_rows, team_stat_rows in zip(team_name_rows, team_stat_rows):
    row_data = list()
    for td in team_name_rows.findChildren('td'):
      row_data.append(td.text)
    for td in team_stat_rows.findChildren('td'):
      row_data.append(td.text)
    stats.append(row_data)
  return stats

# Creates section : column names dictionary
def parse_table_head(thead):
  rows = thead.findChildren('tr')
  sections = rows[0].findChildren('th')
  stat_names = [x.text for x in rows[1].findChildren('th')]
  section_stats_header = OrderedDict()
  curr_col = 0
  for section in sections:
    colspan = int(section['colspan'])
    section_name = section.text.strip()
    section_stats_header[section_name] = stat_names[curr_col: curr_col + colspan]
    curr_col += colspan
  return section_stats_header

# checks if table contains the classes we are loooking for
def is_table_header(table) -> boolean:
  if all(x in table['class'] for x in ['Table__header-group', 'Table__THEAD']):
    return True
  else:
    return False
  
def get_player_gamelog(http_resp) -> list():
  soup = BeautifulSoup(http_resp.text, 'html.parser')
  all_tables = soup.find_all(lambda tag: tag.name=='tbody')
  all_table_heads = soup.find_all(lambda tag: tag.name=='thead')
  
  for thead in all_table_heads:
    if is_table_header(thead):
      section_stats_header = parse_table_head(thead)
      
  stats = parse_gamelog_tbody(all_tables[0])
  complete_gamelog = list()
  
  for row_index in range(0, len(stats) - 1):
    index = 0
    section_with_stats = dict()
    for section in section_stats_header.keys():
      header_with_stats = dict()
      for header in section_stats_header.get(section):
        header_with_stats[header] = stats[row_index][index]
        index += 1
      section_with_stats[section] = header_with_stats
    complete_gamelog.append(section_with_stats)
  return complete_gamelog

# 
# Main Section
#

def get_player_gamelog_per_team(team_initial, player_names) -> dict():
  team_url = team_urls.get(team_initial.upper())
  if team_url is  None: 
    raise Exception("couldn't find url for: " + team_initial)
  
  team_page_resp = requests.get(team_url)
  # has names
  links = get_player_gamelog_links(team_page_resp, player_names)
  player_stats = dict()
  print("Processing team: " + team_initial)
  time.sleep(1.0 + + random.uniform(0, 1))
  for player_name in links.keys():
    player_gamelog = requests.get(links.get(player_name))
    player_stats[player_name] = get_player_gamelog(player_gamelog)
    print("Got player: " + player_name + " stats waiting")
    time.sleep(1.5 + random.uniform(0, 2))
  return player_stats

def get_team_def_stats_table():
  resp = requests.get(team_def_url)
  soup = BeautifulSoup(resp.text, 'html.parser')
  all_tables = soup.find_all(lambda tag: tag.name=='tbody')
  all_table_heads = soup.find_all(lambda tag: tag.name=='thead')
  
  for thead in all_table_heads:
    if is_table_header(thead):
      section_stats_header : OrderedDict = parse_table_head(thead)
  section_stats_header['GP'] = section_stats_header['']
  del section_stats_header['']
  section_stats_header.move_to_end('GP', False)
  section_stats_header['Team'] = ['Team']
  section_stats_header.move_to_end('Team', False)
  stats = pare_team_stats_tbody(all_tables[0], all_tables[1])
  defense_stats = list()
  for row_index in range(0, len(stats) - 1):
    index = 0
    section_with_stats = dict()
    for section in section_stats_header.keys():
      header_with_stats = dict()
      for header in section_stats_header.get(section):
        header_with_stats[header] = stats[row_index][index]
        index += 1
      section_with_stats[section] = header_with_stats
    defense_stats.append(section_with_stats)
  return defense_stats

def get_top_rushing_d(stats, n):
  team_rush_yds_ag = dict()
  for row in stats:
    team_rush_yds_ag[team_name_to_int[row['Team']['Team']]] = float(row['Rushing']['YDS/G'])
  sorted_dict = {k: v for k, v in sorted(team_rush_yds_ag.items(), key=lambda item: item[1])}
  top_5 = take(n, sorted_dict.keys())
  return top_5
  
def get_top_passing_d(stats, n):
  team_rush_yds_ag = dict()
  for row in stats:
    team_rush_yds_ag[team_name_to_int[row['Team']['Team']]] = float(row['Passing']['YDS/G'])
  sorted_dict = {k: v for k, v in sorted(team_rush_yds_ag.items(), key=lambda item: item[1])}
  top_5 = take(n, sorted_dict.keys())
  return top_5

def get_worst_passing_d(stats, n):
  team_rush_yds_ag = dict()
  for row in stats:
    team_rush_yds_ag[team_name_to_int[row['Team']['Team']]] = float(row['Passing']['YDS/G'])
  sorted_dict = {k: v for k, v in sorted(team_rush_yds_ag.items(), key=lambda item: item[1], reverse=True)}
  top_5 = take(n, sorted_dict.keys())
  return top_5
  

def get_worst_rushing_d(stats, n):
  team_rush_yds_ag = dict()
  for row in stats:
    team_rush_yds_ag[team_name_to_int[row['Team']['Team']]] = float(row['Rushing']['YDS/G'])
  sorted_dict = {k: v for k, v in sorted(team_rush_yds_ag.items(), key=lambda item: item[1], reverse=True)}
  top_5 = take(n, sorted_dict.keys())
  return top_5

