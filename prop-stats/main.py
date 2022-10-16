from datetime import date
from io import FileIO
from operator import truediv
from os import stat
import time
from xmlrpc.client import boolean
import requests
from bs4 import BeautifulSoup
from bs4 import Tag
import re
import random

team_urls = [
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
  'https://www.espn.com/nfl/team/stats/_/name/buf/buffalo-bills']


section_names = ['passing', 'rushing', 'receiving']
prop_header={'player': 0, 'team': 1, 'prop': 2}


name_regex = re.compile("^.*?/name/(\w+)/.*?$")
game_regex = re.compile("game:\s.*?", re.IGNORECASE)
passing_prop = re.compile(".*?\s(?:pass|passing)\s.*?", re.IGNORECASE)
rushing_prop = re.compile(".*?\s(?:rush|rushing)\s.*?", re.IGNORECASE)
receiving_prop = re.compile(".*?\s(?:rec|receiving)|(?:receptions)\s.*?", re.IGNORECASE)
yards_prop = re.compile("^.*?(?:yards|yds).*?$", re.IGNORECASE)
attempts_prop = re.compile("^.*?(?:attempts|atts).*?$", re.IGNORECASE)
completions_prop = re.compile("^.*?(?:cmp|completions).*?$", re.IGNORECASE)
tds_prop = re.compile("^.*?(?:tds|touchdowns).*?$", re.IGNORECASE)
int_prop = re.compile("^.*?(?:int|interceptions).*?$", re.IGNORECASE)
receptions_prop = re.compile("^.*?(?:rec|receptions).*?$", re.IGNORECASE)

rec_avg_stats = ['AVG_REC', 'AVG_TGTS', 'AVG_TD', 'AVG_BIG']
rush_avg_stats = ['AVG_ATT', 'AVG_TD', 'AVG_FD', 'AVG_BIG']
passing_avg_stats = ['AVG_CMP', 'AVG_ATT', 'AVG_TD', 'AVG_INT']

def add_index(headers) -> dict:
  return {headers[i]: i for i in range(0, len(headers), 1)}

passing_header = add_index(['GP', 'CMP', 'ATT', 'CMP%', 'YDS', 'AVG', 'YDS/G', "LNG", 'TD', 
  'INT', 'SACK', 'SYL', 'RTG'])
rushing_header = add_index(['GP', 'ATT', 'YDS', 'AVG', 'LNG', 'BIG', 'TD', 'YDS/G', 'FUM', 'LST', 'FD'])
receiving_headres = add_index(['GP', 'REC', 'TGTS', 'YDS', 'AVG', 'TD', 'LNG', 'BIG', 'YDS/G', 'FUM', 
  'LST', 'YAC', 'FD'])



def is_stats_table(table) -> boolean:
  if all(x in table['class'] for x in ['Table', 'Table--align-right']):
    return True
  else:
    return False


def is_name_table(table) -> bool:
  if all(x in table['class'] for x in ['Table--align-right', 'Table--fixed', 'Table--fixed-left']):
    return True
  else:
    return False

def process_name_row(rows) -> list:
  names = list()
  for row in rows:
    cells = row.findChildren('td')
    for cell in cells:
      if cell.text != 'Total':
        name_parts = cell.text.strip().split()
        first_initial = name_parts[0][0:1] + "."
        if len(name_parts) > 3:
          names.append(first_initial + " " + name_parts[1] + " " + name_parts[len(name_parts) - 1])
        else:
          names.append(first_initial + " " + name_parts[1] + " " + name_parts[2])
  return names

def get_names_with_section(all_tables) -> dict:
  table_num = 0
  table_sec = dict()
  for table in all_tables:
    if table_num == 3:
      # only need first 3
      return(table_sec)
    if is_name_table(table):
      rows = table.findChildren(['tr', 'th'])
      table_sec[section_names[table_num]] = process_name_row(rows)
      table_num += 1
  return(table_sec)

def process_stat_row(rows) -> list:
  table = list()
  rows = rows[0:len(rows) - 1]
  for row in rows:
    # Don't process last row
    stat_row = list()
    if len(row.findChildren('td')) > 1:
      for cell in row.findChildren('td'):
        stat_row.append(cell.text)
      table.append(stat_row)
  if len(table) > 0:
    return table
  else:
    return None


def add_team_initials(urls):
  team_urls_enriched = list()
  for url in urls:
    team_initial = name_regex.match(url)
    team_urls_enriched.append([url, team_initial.group(1).upper()])
  return team_urls_enriched
    

def get_stats(all_tables, section_names_dict : dict) -> dict:
  all_stat_rows = list()
  for table in all_tables:
    if is_stats_table(table):
      rows = table.findChildren(['tr'])
      section_rows = process_stat_row(rows)
      if section_rows is not None:
        for stat_row in section_rows:
          if stat_row is not None:
            all_stat_rows.append(stat_row)

  stat_row_index = 0
  finished_data = list()
  for section in section_names_dict:
    for player_name in section_names_dict.get(section):
      finished_data.append(enrich_stats(all_stat_rows[stat_row_index], player_name, section))
      stat_row_index += 1

  return finished_data


def enrich_stats(stats, player_name, section):
  averge_stats = dict()
  averge_stats["NAME"] = player_name
  averge_stats["SECTION"] = section
  if section == 'passing':
    enrich_passing(stats, averge_stats)
  elif section == 'rushing':
    enrich_rushing(stats, averge_stats)
  elif section == 'receiving':
    enrich_rec(stats, averge_stats)
  return averge_stats


def get_avg(stat_name, header_name, averge_stats, stats, header):
  averge_stats[stat_name] = '%.2f' % (float(stats[header.get(header_name)]
    .replace(',','')) / float(stats[header.get('GP')]))
  
def enrich_passing(pass_stats, averge_stats):
  for stat_name in passing_avg_stats:
    get_avg(stat_name, stat_name[stat_name.rindex("_") + 1:], averge_stats, pass_stats, passing_header)
  averge_stats['CMP%'] = pass_stats[passing_header.get('CMP%')]
  averge_stats['YDS_PER_GAME'] = pass_stats[passing_header.get('YDS/G')]
  averge_stats['PASS_RATING'] = pass_stats[passing_header.get('RTG')]

def enrich_rushing(rushing_stats, averge_stats):
  for stat_name in rush_avg_stats:
    get_avg(stat_name, stat_name[stat_name.rindex("_") + 1:], averge_stats, rushing_stats, rushing_header)
  averge_stats['YDS_PER_RUSH'] = rushing_stats[rushing_header.get('AVG')]
  averge_stats['YDS_PER_GAME'] = rushing_stats[rushing_header.get('YDS/G')]

rec_avg_stats = ['AVG_REC', 'AVG_TGTS', 'AVG_TD', 'AVG_BIG']
def enrich_rec(rec_stats, averge_stats):
  for stat_name in rec_avg_stats:
    get_avg(stat_name, stat_name[stat_name.rindex("_") + 1:], averge_stats, rec_stats, receiving_headres)
  averge_stats['YDS_PER_CATCH'] = rec_stats[receiving_headres.get('AVG')]
  averge_stats['YDS_PER_GAME'] = rec_stats[receiving_headres.get('YDS/G')]


def get_section(team_stats, section) -> list:
  if team_stats is not None:
    return [player_stats for player_stats in team_stats if player_stats['SECTION'] == section]
  else:
    raise Exception("team was not found in scraped stats")

def split_prop_line(line):
  if len(line.split(",")) == 3:
    return line.split(",")
  else:
    raise Exception(line + " did not have three sections")

def process_pass_prop(line, new_file, all_stats):
  prop_line = split_prop_line(line)
  player_name = prop_line[prop_header.get('player')].strip()
  team = prop_line[prop_header.get('team')].strip()
  print("Getting team: " + team)
  team_stats = all_stats.get(team)
  line = line.strip()
  prop = prop_line[prop_header.get('prop')].strip()
  for pass_stats in get_section(team_stats, section_names[0]):
    if pass_stats['NAME'].lower() == player_name.lower():
      if bool(yards_prop.match(prop)):
        new_file.write(line + ', AVG_ATT ' + pass_stats['AVG_ATT'] + ', CMP% ' + pass_stats['CMP%']
                       + ', YDS_PER_GAME ' + pass_stats['YDS_PER_GAME'] + ', PASS_RATING ' + pass_stats['PASS_RATING'] + "\n")
        return
      elif bool(attempts_prop.match(prop)):
        new_file.write(line + ', AVG_ATT ' + pass_stats['AVG_ATT'] + "\n")
        return
      elif bool(completions_prop.match(prop)):
         new_file.write(line + ', AVG_ATT ' + pass_stats['AVG_ATT'] + ', AVG_CMP ' + pass_stats['AVG_CMP'] + 
                        ', CMP% ' + pass_stats['CMP%'] + '\n')
         return
      elif bool(tds_prop.match(prop)):
        new_file.write(line + ', AVG_ATT ' + pass_stats['AVG_ATT'] + ', AVG_TD ' + pass_stats['AVG_TD'] + '\n')
        return
      elif bool(int_prop.match(prop)):
        new_file.write(line + ', AVG_ATT ' + pass_stats['AVG_ATT'] + ', AVG_INT ' + pass_stats['AVG_INT'] + "\n")
        return
      else:
        print("no prop category found, doing all stats" + prop)
        new_file.write("- " + line.strip() + ";" + ' AVG_CMP ' + pass_stats['AVG_CMP'] + ', AVG_ATT ' + pass_stats['AVG_ATT'] 
        + ', CMP% ' + pass_stats['CMP%'] + ', YDS_PER_GAME ' + pass_stats['YDS_PER_GAME'] + ', AVG_TD ' 
        + pass_stats['AVG_TD'] + ', AVG_INT ' + pass_stats['AVG_INT'] + ', PASS_RATING ' + pass_stats['PASS_RATING'] + "\n")
        return
  new_file.write(line + ',' + " no stats founds \n")

def process_rush_prop(line, new_file, all_stats):
  prop_line = split_prop_line(line)
  player_name = prop_line[prop_header.get('player')].strip()
  team = prop_line[prop_header.get('team')].strip()
  team_stats = all_stats.get(team)
  line = line.strip()
  prop = prop_line[prop_header.get('prop')].strip()
  for rush_stats in get_section(team_stats, section_names[1]):
    if rush_stats['NAME'].lower() == player_name.lower():
      if bool(yards_prop.match(prop)):
        new_file.write(line + ', AVG_ATT ' + rush_stats['AVG_ATT'] + ', YDS_PER_RUSH ' + rush_stats['YDS_PER_RUSH']
                       + ', YDS_PER_GAME ' + rush_stats['YDS_PER_GAME'] + "\n")
        return
      elif bool(attempts_prop.match(prop)):
        new_file.write(line + ', AVG_ATT ' + rush_stats['AVG_ATT'] + "\n")
        return
      elif bool(tds_prop.match(prop)):
        new_file.write(line + ', AVG_ATT ' + rush_stats['AVG_ATT'] + ', AVG_TD ' + rush_stats['AVG_TD'] + "\n")
        return
      else: 
        print("no prop category found, doing all stats: " + prop)
        new_file.write(line + ', AVG_ATT ' + rush_stats['AVG_ATT'] + ', YDS_PER_RUSH ' 
        + rush_stats['YDS_PER_RUSH'] + ', YDS_PER_GAME ' + rush_stats['YDS_PER_GAME'] 
        + ', AVG_TD ' + rush_stats['AVG_TD'] + ', AVG_FD ' + rush_stats['AVG_FD'] 
        + ', AVG_BIG ' + rush_stats['AVG_BIG'] + "\n")
        return
  new_file.write("- " + line.strip() + ',' + " no stats founds \n")

# e_rec_head = add_index(['NAME', 'SECTION', 'AVG_REC', 'AVG_TGTS', 'YDS_PER_CATCH', 'YDS_PER_GAME', 'AVG_TD', 'AVG_BIG'])
def process_rec_prop(line, new_file, all_stats):
  prop_line = split_prop_line(line)
  player_name = prop_line[prop_header.get('player')].strip()
  team = prop_line[prop_header.get('team')].strip()
  team_stats = all_stats.get(team)
  line = line.strip()
  prop = prop_line[prop_header.get('prop')].strip()
  for rec_stats in get_section(team_stats, section_names[2]):
    if rec_stats['NAME'].lower() == player_name.lower():
      if bool(yards_prop.match(prop)):
        new_file.write(line + ', AVG_REC ' + rec_stats['AVG_REC'] + ', AVG_TGTS ' 
        + rec_stats['AVG_TGTS'] + ', YDS_PER_CATCH ' + rec_stats['YDS_PER_CATCH'] + ', YDS_PER_GAME ' 
        + rec_stats['YDS_PER_GAME'] + '\n')
        return
      if bool(receptions_prop.match(prop)):
        new_file.write(line + ', AVG_REC ' + rec_stats['AVG_REC'] + ', AVG_TGTS ' 
        + rec_stats['AVG_TGTS'] + '\n')
        return
      if bool(tds_prop.match(prop)):
        new_file.write(line + ', AVG_REC ' + rec_stats['AVG_REC'] + ', AVG_TGTS ' 
        + rec_stats['AVG_TGTS'] + ', AVG_TD ' + rec_stats['AVG_TD'] + '\n')
        return
      else:
        print("no prop category found, doing all stats: " + prop)
        new_file.write("- " + line.strip() + ";" + ', AVG_REC ' + rec_stats['AVG_REC'] + ', AVG_TGTS ' 
        + rec_stats['AVG_TGTS'] + ', YDS_PER_CATCH ' + rec_stats['YDS_PER_CATCH'] + ', YDS_PER_GAME ' 
        + rec_stats['YDS_PER_GAME'] + ', AVG_TD ' + rec_stats['AVG_TD'] + ', AVG_BIG ' + rec_stats['AVG_BIG'] + "\n")
        return
  new_file.write("- " + line.strip() + ';' + " no stats founds \n")


def process_prop_line(line, new_file, all_stats): 
  if(bool(passing_prop.match(line))):
    process_pass_prop(line, new_file, all_stats)
  elif(bool(rushing_prop.match(line))):
    process_rush_prop(line, new_file, all_stats)
  elif(bool(receiving_prop.match(line))):
    process_rec_prop(line, new_file, all_stats)

def process_prop_list(file, new_file, all_stats):
  for line in file:
    # print(line + str(bool(game_regex.search(line, re.IGNORECASE))))
    if(len(line.strip()) == 0):
      continue
    elif(line[0] == '#'):
      continue
    elif(bool(game_regex.match(line))):
      print('Processing Game: ' + line)
      new_file.write("\n" + line.strip() + "\n\n")
    else: 
      process_prop_line(line, new_file, all_stats)


# print(passing_avg_stats[0][passing_avg_stats[0].rindex("_") + 1 :])

# Main
team_urls = add_team_initials(team_urls)
team_stats = dict()

for team_url in team_urls:
  print('Getting: ' + str(team_url) + "\n")
  resp = requests.get(team_url[0])
  time.sleep(1.5 + random.uniform(0, 2))
  soup = BeautifulSoup(resp.text, 'html.parser')
  all_tables = soup.find_all(lambda tag: tag.name=='table')
  team_stats[team_url[1]] = (get_stats(all_tables, get_names_with_section(all_tables)))
 

f = open("filled-out.txt", "r")
new_f = open(str(int(time.time())) + "-props.txt", 'a')
process_prop_list(f, new_f, team_stats)

new_f.close()