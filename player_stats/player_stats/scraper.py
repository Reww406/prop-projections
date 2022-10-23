r"""
    This py file scrapes websites for betting data.
"""

import re
import random
import time
from typing import OrderedDict
from more_itertools import take
import requests
from bs4 import BeautifulSoup, SoupStrainer

NAME_REGEX = re.compile(r"^.*?/name/(\w+)/(.*?)$", re.IGNORECASE)
PLAYER_LINK = re.compile(r"^.*/player/.*?\d+/([a-zA-Z]+)-([a-zA-Z]+).*?$")

TEAM_DEF_URL = 'https://www.espn.in/nfl/stats/team/_/view/defense/teams/8'
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36(KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A",
]


def add_team_initials(urls):
    r"""
        Takes team URLS and changes them to initial : team_url
    """
    team_urls_enriched = {}
    for url in urls:
        team_initial = NAME_REGEX.match(url)
        team_urls_enriched[team_initial.group(1).upper()] = url
    return team_urls_enriched


def create_team_name_to_int(team_urls):
    r"""
        Creates dict with team_name : initial
    """
    team_name_to_int = {}
    for url in team_urls.values():
        match = NAME_REGEX.match(url.strip())
        name = ""
        for name_part in match.group(2).split("-"):
            name += name_part.strip().capitalize() + " "
        name = name.strip()
        team_name_to_int[name] = match.group(1).upper()
    return team_name_to_int


DK_NFL_PAGE = "https://sportsbook.draftkings.com/leagues/football/nfl"
INT_TEAM_URL = add_team_initials([
    "https://www.espn.com/nfl/team/stats/_/name/mia/miami-dolphins",
    "https://www.espn.com/nfl/team/stats/_/name/dal/dallas-cowboys",
    "https://www.espn.com/nfl/team/stats/_/name/nyg/new-york-giants",
    "https://www.espn.com/nfl/team/stats/_/name/phi/philadelphia-eagles",
    "https://www.espn.com/nfl/team/stats/_/name/wsh/washington-commanders",
    "https://www.espn.com/nfl/team/stats/_/name/chi/chicago-bears",
    "https://www.espn.com/nfl/team/stats/_/name/det/detroit-lions",
    "https://www.espn.com/nfl/team/stats/_/name/gb/green-bay-packers",
    "https://www.espn.com/nfl/team/stats/_/name/min/minnesota-vikings",
    "https://www.espn.com/nfl/team/stats/_/name/atl/atlanta-falcons",
    "https://www.espn.com/nfl/team/stats/_/name/car/carolina-panthers",
    "https://www.espn.com/nfl/team/stats/_/name/no/new-orleans-saints",
    "https://www.espn.com/nfl/team/stats/_/name/tb/tampa-bay-buccaneers",
    "https://www.espn.com/nfl/team/stats/_/name/ari/arizona-cardinals",
    "https://www.espn.com/nfl/team/stats/_/name/lar/los-angeles-rams",
    "https://www.espn.com/nfl/team/stats/_/name/sf/san-francisco-49ers",
    "https://www.espn.com/nfl/team/stats/_/name/sea/seattle-seahawks",
    "https://www.espn.com/nfl/team/stats/_/name/lac/los-angeles-chargers",
    "https://www.espn.com/nfl/team/stats/_/name/ne/new-england-patriots",
    "https://www.espn.com/nfl/team/stats/_/name/nyj/new-york-jets",
    "https://www.espn.com/nfl/team/stats/_/name/bal/baltimore-ravens",
    "https://www.espn.com/nfl/team/stats/_/name/cin/cincinnati-bengals",
    "https://www.espn.com/nfl/team/stats/_/name/cle/cleveland-browns",
    "https://www.espn.com/nfl/team/stats/_/name/pit/pittsburgh-steelers",
    "https://www.espn.com/nfl/team/stats/_/name/hou/houston-texans",
    "https://www.espn.com/nfl/team/stats/_/name/ind/indianapolis-colts",
    "https://www.espn.com/nfl/team/stats/_/name/jax/jacksonville-jaguars",
    "https://www.espn.com/nfl/team/stats/_/name/ten/tennessee-titans",
    "https://www.espn.com/nfl/team/stats/_/name/den/denver-broncos",
    "https://www.espn.com/nfl/team/stats/_/name/kc/kansas-city-chiefs",
    "https://www.espn.com/nfl/team/stats/_/name/lv/las-vegas-raiders",
    "https://www.espn.com/nfl/team/stats/_/name/buf/buffalo-bills",
])

TEAM_NAME_TO_INT = create_team_name_to_int(INT_TEAM_URL)


def request_with_spoof(url):
    r"""
        Rotates IP and user agent for request
    """
    random_ua = USER_AGENTS[random.randint(0, 2)]
    headers = {"User-Agent": random_ua}
    return requests.get(url, headers=headers, timeout=30)


# Get links for players in player_names
def get_player_gamelog_links(team_page, player_names: list()) -> dict():
    r"""
    Gets ESPN links for players passed in player_names
    :param player_names list of players that should be grabbed from ESPN
    :param team_page html for ESPN team page, from requests
    """

    name_link = {}
    for link in BeautifulSoup(team_page.text,
                              "html.parser",
                              parse_only=SoupStrainer("a")):
        if not link.has_attr("href"):
            continue
        match = PLAYER_LINK.match(link["href"])
        if match is not None:
            # Get first inital and name
            name = (match.group(1).strip()[0:1].upper() + "." + " " +
                    match.group(2).strip().capitalize())
            if name not in player_names:
                continue
            if name not in name_link.keys():
                link = match.group(0)
                stats_link = (link[:link.index("_") - 1] + "/gamelog" +
                              link[link.index("_") - 1:])
                name_link[name] = stats_link
    return name_link


# Creates 2D array of table
def parse_gamelog_tbody(tbody):
    r"""
    Creates 2D Array from a beatifulSoup element
    """
    stats = []
    for row in tbody.findChildren("tr"):
        row_data = []
        for td in row.findChildren("td"):
            row_data.append(td.text)
        stats.append(row_data)
    return stats


def pare_team_stats_tbody(team_name_tb, stats_tb):
    r"""
    Creates 2D Array from beatiful soup table.
    will zip team name and stats togther before creating array
    """

    stats = []
    team_name_rows = team_name_tb.findChildren("tr")
    team_stat_rows = stats_tb.findChildren("tr")
    for team_name_rows, team_stat_rows in zip(team_name_rows, team_stat_rows):
        row_data = []
        for td in team_name_rows.findChildren("td"):
            row_data.append(td.text)
        for td in team_stat_rows.findChildren("td"):
            row_data.append(td.text)
        stats.append(row_data)
    return stats


def parse_table_head(thead):
    r"""
    Creates a ordered dictionary with \{section : \[headers\]\}
    Uses colspan html attribute to decide how many headers to put in
    each section
    """

    section_stats_header = OrderedDict()
    rows = thead.findChildren("tr")
    sections = rows[0].findChildren("th")
    stat_names = [x.text for x in rows[1].findChildren("th")]
    curr_col = 0
    for section in sections:
        colspan = int(section["colspan"])
        section_name = section.text.strip()
        section_stats_header[section_name] = stat_names[curr_col:curr_col +
                                                        colspan]
        curr_col += colspan
    return section_stats_header


# checks if table contains the classes we are loooking for
def is_table_header(table):
    r"""
        Checks if table header has correct attributes
    """
    return all(x in table["class"]
               for x in ["Table__header-group", "Table__THEAD"])


def get_player_gamelog_per_team(team_initial, player_names):
    r"""
        Get game log for players from ESPN, return player_name: stats
    """
    team_url = INT_TEAM_URL.get(team_initial.upper())
    if team_url is None:
        raise Exception("couldn't find url for: " + team_initial)

    team_page_resp = request_with_spoof(team_url)
    # has names
    links = get_player_gamelog_links(team_page_resp, player_names)
    player_stats = {}
    print("Processing team: " + team_initial)
    for player_name in links.keys():
        player_gamelog = request_with_spoof(links.get(player_name))
        player_stats[player_name] = get_player_gamelog(player_gamelog)
        print("Got player: " + player_name + " stats waiting")
        time.sleep(1.5 + random.uniform(0, 2))
    return player_stats


def get_player_gamelog(http_resp):
    r"""
        Parse stats from gamelog html
    """
    soup = BeautifulSoup(http_resp.text, "html.parser")
    all_tables = soup.find_all(lambda tag: tag.name == "tbody")
    all_table_heads = soup.find_all(lambda tag: tag.name == "thead")

    for thead in all_table_heads:
        if is_table_header(thead):
            section_stats_header = parse_table_head(thead)

    stats = parse_gamelog_tbody(all_tables[0])
    complete_gamelog = []

    for row_index in range(0, len(stats) - 1):
        index = 0
        section_with_stats = {}
        for section in section_stats_header.keys():
            header_with_stats = {}
            for header in section_stats_header.get(section):
                header_with_stats[header] = stats[row_index][index]
                index += 1
            section_with_stats[section] = header_with_stats
        complete_gamelog.append(section_with_stats)
    return complete_gamelog


def get_team_def_stats_table():
    r"""
        Get team stats from ESPN, this is yds against passing and rushing
    """
    resp = request_with_spoof(TEAM_DEF_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    all_tables = soup.find_all(lambda tag: tag.name == "tbody")
    all_table_heads = soup.find_all(lambda tag: tag.name == "thead")

    for thead in all_table_heads:
        if is_table_header(thead):
            section_stats_header: OrderedDict = parse_table_head(thead)
    section_stats_header["GP"] = section_stats_header[""]
    del section_stats_header[""]
    section_stats_header.move_to_end("GP", False)
    section_stats_header["Team"] = ["Team"]
    section_stats_header.move_to_end("Team", False)
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


def get_games_from_dk():
    r"""
        Get Prop bets that DK has posted
    """
    # resp = request_with_spoof(DK_NFL_PAGE)
    # soup = BeautifulSoup(resp.text, "html.parser")
    # print(resp.text)
    # tbody = soup.find_all(lambda tag: tag.name == "table")


def get_top_n_team_stats(stats, n, section, reverse_order):
    r"""
        Get top n teams from team stats used to get top 5 worst/best defenses
        Returns team intials
    """
    team_stats = {}
    for row in stats:
        team_stats[TEAM_NAME_TO_INT[row["Team"]["Team"]]] = float(
            row[section]["YDS/G"])
        sorted_dict = dict(
            sorted(team_stats.items(),
                   key=lambda item: item[1],
                   reverse=reverse_order))

    return take(n, sorted_dict.keys())


get_games_from_dk()
