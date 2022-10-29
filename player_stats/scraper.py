r"""
    This py file scrapes websites for betting data.
"""

import re
import random
import time
from typing import OrderedDict
# from selenium import webdriver
from more_itertools import take
from numpy import true_divide
from pexpect import ExceptionPexpect
import requests
from seleniumwire import webdriver
from bs4 import BeautifulSoup, SoupStrainer
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

#
# Costants
#


# Used to generate constant
def add_team_initials(urls):
    r"""
        Takes team URLS and changes them to initial : team_url
    """
    team_urls_enriched = {}
    for url in urls:
        team_initial = NAME_LINK_REGEX.match(url)
        team_urls_enriched[team_initial.group(1).upper()] = url
    return team_urls_enriched


# Used to generate constant
def create_team_name_to_int(team_urls):
    r"""
        Creates dict with team_name : initial
    """
    team_name_to_int = {}
    for url in team_urls.values():
        match = NAME_LINK_REGEX.match(url.strip())
        name = ""
        for name_part in match.group(2).split("-"):
            name += name_part.strip().capitalize() + " "
        name = name.strip()
        team_name_to_int[name] = match.group(1).upper()
    return team_name_to_int


def create_draft_edge_to_int(team_urls):
    r"""
        Creates dict with team_name : initial
    """
    team_name_to_int = {}
    for url in team_urls.values():
        match = NAME_LINK_REGEX.match(url.strip())
        name = ""
        name = match.group(2).split("-")[len(match.group(2).split("-")) -
                                         1].capitalize().strip()
        team_name_to_int[name] = match.group(1).upper()
    return team_name_to_int


NAME_LINK_REGEX = re.compile(r"^.*?/name/(\w+)/(.*?)$", re.IGNORECASE)
REGULAR_SESSION_REGEX = re.compile(r"^\d{4}\sRegular.*?$")
PLAYER_LINK_REGEX = re.compile(
    r"^.*/player/.*?\d+/([a-zA-Z]+)-([a-zA-Z]+).*?$")
SPREAD_REGEX = re.compile(r"^([\-\+]{1}[\d]+\.?[5]?).*?$")
DK_NAME_REGEX = re.compile(r"^(.*?)[(]\w+[)]$")
TOTAL_REGEX = re.compile(r".*?\s([\d]+.*?)")
RANKING_FOR_POS_REGEX = {
    "qb": re.compile(r"addpointer\smyrow\srow_qb.*?"),
    "rb": re.compile(r"addpointer\smyrow\srow_rb.*?"),
    "wr": re.compile(r"addpointer\smyrow\srow_wr.*?"),
    "te": re.compile(r"addpointer\smyrow\srow_te.*?")
}
ESPN_GAME_LOG_YEAR_REGEX = re.compile(r"^(.*?/id/[\d]+/).*?$")

LAST_YEAR = '2021'
CURRENT_YEAR = '2022'
GAMELOG_YEAR_URI = "type/nfl/year/" + LAST_YEAR

DRAFT_EDGE_URL = "https://draftedge.com/nfl-defense-vs-pos/"
TEAM_DEF_URL = 'https://www.espn.in/nfl/stats/team/_/view/defense/teams/8'
DK_BASE_PAGE_URL = "https://sportsbook.draftkings.com"
DK_NFL_PAGE_URL = "https://sportsbook.draftkings.com/leagues/football/nfl"
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

DRAFT_EDGE_TO_INT = create_draft_edge_to_int(INT_TEAM_URL)

PROPS_TO_PARSE = [
    "Pass Yds", "Pass Completions", "Pass Attempts", "Rush Yds", "Rec Yds",
    "Receptions", "Rush Attempts"
]

DK_TO_ESPN_NAME_CONV = {
    "NY Jets": "NYJ",
    'WAS Commanders': 'WSH',
    'NY Giants': 'NYG',
    'LA Rams': 'LAR',
    'LA Chargers': 'LAC'
}

TEAM_NAME_TO_INT = create_team_name_to_int(INT_TEAM_URL)
PASSING_PROP_URI = "passing-props"
RUSH_AND_REC_PROP_URI = "rush/rec-props"

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36(KHTML, "
    + "like Gecko) Chrome/104.0.5112.79 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, "
    + "like Gecko) Version/7.0.3 Safari/7046A194A",
]

PROXY_FILE = open("proxy_pass.txt", "r", encoding="UTF-8")
USERNAME = PROXY_FILE.readline().strip()
PASSWORD = PROXY_FILE.readline().strip()
PROXY_FILE.close()

PROXY_URL = "http://customer-" + USERNAME + "-cc-US:" + PASSWORD + "@pr.oxylabs.io:7777"

PROXIES = {"http": PROXY_URL, "https": PROXY_URL}

CHROME_OPTIONS = webdriver.ChromeOptions()
CAPS = DesiredCapabilities().CHROME
CAPS["pageLoadStrategy"] = "normal"
PREFS = {
    'profile.default_content_setting_values': {
        'images': 2,
        'popups': 2,
        'notifications': 2,
        'mouselock': 2,
        'push_messaging': 2,
    }
}

CHROM_DRIVER_PATH = "/usr/bin/chromedriver"
CHROME_OPTIONS.add_experimental_option("prefs", PREFS)
OPTIONS = {'proxy': {'http': PROXY_URL, 'https': PROXY_URL}}

CAPABILITIES = webdriver.DesiredCapabilities.CHROME

DRIVER = webdriver.Chrome(CHROM_DRIVER_PATH,
                          seleniumwire_options=OPTIONS,
                          chrome_options=CHROME_OPTIONS,
                          desired_capabilities=CAPABILITIES)
print("Driver inialized..")


#
# HTTP Functions
#
def request_with_spoof(url):
    r"""
        Rotates IP and user agent for request
    """
    random_ua = USER_AGENTS[random.randint(0, 2)]
    headers = {"User-Agent": random_ua}
    return requests.get(url, headers=headers, timeout=30, proxies=PROXIES)


def get_prop_page_source(url):
    r"""
        Get page text using Selenium
    """
    print("Getting: " + url)
    DRIVER.get(url)
    try:
        WebDriverWait(DRIVER, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 ".sportsbook-responsive-card-container__body")))
        return DRIVER.page_source
    except TimeoutException:
        print("timed out..")
    return DRIVER.page_source


def get_page_text(url):
    r"""
        Get page text using Selenium
    """
    print("Getting: " + url)
    DRIVER.get(url)
    return DRIVER.page_source


#
# ESPN Scraping
#
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
        match = PLAYER_LINK_REGEX.match(link["href"])
        if match is not None:
            # Get first inital and name
            name = (match.group(1).strip()[0:1].upper() + ". " +
                    match.group(2).strip().capitalize())
            if name not in player_names:
                continue
            if name not in name_link:
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
        for t_data in row.findChildren("td"):
            row_data.append(t_data.text)
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
        for t_data in team_name_rows.findChildren("td"):
            row_data.append(t_data.text)
        for t_data in team_stat_rows.findChildren("td"):
            row_data.append(t_data.text)
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


def is_table_header(table):
    """_summary_

    Args:
        table (_type_): _description_

    Returns:
        _type_: _description_
    """
    return all(x in table["class"]
               for x in ["Table__header-group", "Table__THEAD"])


# checks if table contains the classes we are loooking for
def is_regular_season_header(table):
    r"""
        Checks if table header has correct attributes
    """
    if all(x in table["class"]
           for x in ["Table__header-group", "Table__THEAD"]):
        tr = table.find('tr')
        th = tr.find("th", {"class": ["Table__TH"]})
        if REGULAR_SESSION_REGEX.match(th.text):
            return True
    return False


#https://www.espn.com/nfl/player/gamelog/_/id/4241479/type/nfl/year/2021
#https://www.espn.com/nfl/player/gamelog/_/id/4241479/tua-tagovailoa


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
    for player_name in links:
        gamelogs = {}
        current_year_gl = request_with_spoof(links.get(player_name))
        try:
            last_years_link = ESPN_GAME_LOG_YEAR_REGEX.match(
                links.get(player_name)).group(1) + GAMELOG_YEAR_URI
            last_year_gamelog = request_with_spoof(last_years_link)
            gamelogs[LAST_YEAR] = get_player_gamelog(last_year_gamelog)
        except Exception:
            print(f"Can't get {player_name} stats from 2021")
        gamelogs[CURRENT_YEAR] = get_player_gamelog(current_year_gl)
        player_stats[player_name] = gamelogs
        print("Got player: " + player_name)

    return player_stats


def get_player_gamelog(http_resp):
    r"""
        Parse stats from gamelog html
    """
    soup = BeautifulSoup(http_resp.text, "html.parser")
    all_tables = soup.find_all(lambda tag: tag.name == "tbody")
    all_table_heads = soup.find_all(lambda tag: tag.name == "thead")

    for thead in all_table_heads:
        if is_regular_season_header(thead):
            print("Found Regular season header")
            section_stats_header = parse_table_head(thead)
    if len(all_tables) > 2:
        stats = parse_gamelog_tbody(all_tables[1])
    else:
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
    defense_stats = []
    for row_index in range(0, len(stats) - 1):
        index = 0
        section_with_stats = {}
        for section in section_stats_header.keys():
            header_with_stats = {}
            for header in section_stats_header.get(section):
                header_with_stats[header] = stats[row_index][index]
                index += 1
            section_with_stats[section] = header_with_stats
        defense_stats.append(section_with_stats)
    return defense_stats


#
# DK Functions
#
def is_prop_link(link):
    """
        Check if table contains prop links
    """
    if link.get('class') is None or len(link.get('class')) == 0:
        return False
    if link['class'][0].lower() == 'sportsbook-tabbed-subheader__tab-link':
        return True
    return False


def get_top_n_team_stats(stats, num, section, reverse_order):
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

    return take(num, sorted_dict.keys())


def dk_team_to_int(team_name):
    """
        Takes DK team name and converts to match ESPN
    """
    if team_name in DK_TO_ESPN_NAME_CONV:
        print("Changing: " + team_name)
        return DK_TO_ESPN_NAME_CONV.get(team_name)
    return team_name.split()[0].strip()


def get_team_name(prop_page):
    """
        Parses DK team name out of page title and converts to match ESPN
    """
    soup = BeautifulSoup(prop_page, "html.parser")
    teams = re.sub("AT", "@", [
        div.text for div in soup.find_all(
            "div", {"class": {"event-page-countdown-timer__title"}})
    ][0]).split("@")
    return dk_team_to_int(teams[0]) + " @ " + dk_team_to_int(teams[1])


def get_prop_pages(game_page_soup):
    """
        Takes DK game page link, and returns {CHI @ WSH: [prop1, prop2 }
    """
    links = game_page_soup.findAll('a', href=True)
    pages = []
    game = ""
    for game_link in links:
        if is_prop_link(game_link):
            if game_link['href'].find(PASSING_PROP_URI) != -1:
                passing_page = get_prop_page_source(DK_BASE_PAGE_URL +
                                                    game_link['href'])
                pages.append(passing_page)
                game = get_team_name(passing_page)
            elif game_link['href'].find(RUSH_AND_REC_PROP_URI) != -1:
                rushing_page = get_prop_page_source(DK_BASE_PAGE_URL +
                                                    game_link['href'])
                pages.append(rushing_page)
                game = get_team_name(rushing_page)
    return {game: pages}


def get_game_spread(game_page_soup):
    """
        Takes DK game page link, and return {Spread: {CHI: "+4", "WSH -4}}
    """

    spread_table = game_page_soup.find("tbody",
                                       {"class": ["sportsbook-table__body"]})
    spread_dict = {}
    for t_row in spread_table.findAll('tr'):
        team_name = dk_team_to_int(
            t_row.find("th", {
                "class": ["sportsbook-table__column-row"]
            }).text)
        tds = t_row.findAll("td", {"class": ["sportsbook-table__column-row"]})
        spread = SPREAD_REGEX.match(tds[0].text).group(1)

        spread_dict[team_name] = spread
    return {"Spread": spread_dict}


def get_game_total(game_page_soup):
    """
        Takes DK game page
    """
    total_table = game_page_soup.find("tbody",
                                      {"class": ["sportsbook-table__body"]})
    t_row = total_table.find('tr')
    tds = t_row.findAll("td", {"class": ["sportsbook-table__column-row"]})
    print(tds[1].text)
    total = TOTAL_REGEX.match(tds[1].text).group(1)
    return {"Total": total}


def get_games_from_dk(table_num):
    r"""
        Takes, table_num as in which section to grab from main NFL page
        Get Prop bets that DK has posted

        return [{CHI @ WSH: [prop_page, prop_page]},
                {Spread: {CHI: "+4", "WSH": "-4"}}, {Total: "45"}}]
    """
    start_time = int(time.time())
    resp = get_page_text(DK_NFL_PAGE_URL)
    scraped_pages = []
    soup = BeautifulSoup(resp, "html.parser")
    table_links = soup.find_all(
        lambda tag: tag.name == "table")[table_num].findAll('a', href=True)
    for game_link in table_links:
        if game_link['href'].find("sgp") != -1:
            # Don't process SGP link
            continue
        next_link = DK_BASE_PAGE_URL + game_link['href']
        if next_link in scraped_pages:
            continue
        scraped_pages.append(next_link)
        soup = BeautifulSoup(get_page_text(next_link), "html.parser")
        prop_pages = get_prop_pages(soup)
        spread = get_game_spread(soup)
        total = get_game_total(soup)
    print("Took: " + str(int(time.time()) - start_time) + " seconds")
    return [prop_pages, spread, total]


def fix_odds(text):
    """
        Turns odds into o32, +200
    """
    plus_index = text.find('+')
    seperator = ""
    if plus_index != -1:
        seperator = "+"
    else:
        seperator = "−"
    text = re.sub(r'O\s', 'o', text)
    text = re.sub(r'U\s', 'u', text)
    sections = text.split(seperator)
    return sections[0] + " " + seperator + sections[1]


def get_player_team(team_pages, player_name):
    """
        Takes a player name with two possible teams
        and finds which one he is on
    """
    for url in team_pages:
        for link in BeautifulSoup(team_pages.get(url),
                                  "html.parser",
                                  parse_only=SoupStrainer("a")):
            if len(link.text) <= 0:
                continue
            if link.text.lower().find(player_name.lower()) != -1:
                team_initial = NAME_LINK_REGEX.match(url)
                return team_initial.group(1).upper()
    return "TNF"


def create_espn_player_name(name):
    """_
        turns full name into T. Tuagivilla
    """
    return name.split()[0][0:1] + ". " + name.split()[1]


def process_dk_prop_pages(dk_prop_dict):
    """
        Extract Prop bets from DK pass Prop section
        {game_name: [props, props]}
    """
    game = next(iter(dk_prop_dict))
    team_pages = {}
    teams = [x.strip() for x in game.split('@')]
    print(str(teams))
    for url in [INT_TEAM_URL[x] for x in teams]:
        team_pages[url] = request_with_spoof(url).text
    props = []
    for text in dk_prop_dict.get(game):
        accordian_divs = BeautifulSoup(text, "html.parser").find_all(
            "div",
            {"class": ["sportsbook-event-accordian__wrapper", "expanded"]})
        for div in accordian_divs:
            title = div.find(
                'a',
                {"class": ["sportsbook-event-accordion__title", "active"]})
            if title is None or title.text not in PROPS_TO_PARSE:
                # Process first div
                continue
            for row in div.find('tbody').findAll('tr'):
                match = DK_NAME_REGEX.match(row.find('th').text)
                if match is not None:
                    player_name = match.group(1).strip()
                else:
                    player_name = row.find('th').text.strip()
                team_name = get_player_team(team_pages, player_name)
                data = [player_name, team_name, title.text]
                for t_data in row.findAll('td'):
                    if t_data.text.find("O") != -1:
                        data.append(fix_odds(t_data.text))
                props.append(data)
    return props


def get_pos_defense_ranking(html_class):
    """
        Gets ranking of teams by poistion.
    """
    resp = request_with_spoof(DRAFT_EDGE_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.find('tbody').find_all("tr", {"class": html_class})
    defense_rank = {}
    for row in rows:
        tds = row.find_all('td')
        defense_rank[DRAFT_EDGE_TO_INT.get(tds[0].text.strip())] = float(
            tds[2].text)
    return defense_rank


def get_top_n_def_for_pos(defense_stats, num, worst):
    r"""
        Get to N stats for position defense ranking, higher number worse..
    """
    sorted_dict = dict(
        sorted(defense_stats.items(), key=lambda item: item[1], reverse=worst))

    return take(num, sorted_dict.keys())


def driver_quit():
    """
        Quit Driver
    """
    DRIVER.quit()
