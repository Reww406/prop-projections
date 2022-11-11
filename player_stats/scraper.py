r"""
    This py file scrapes websites for betting data.
"""

import re
import random
import time
from typing import OrderedDict
from requests import HTTPError, ConnectTimeout, ReadTimeout
from more_itertools import take
import requests
from seleniumwire import webdriver
from bs4 import BeautifulSoup, SoupStrainer
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


# Used to generate constant
def add_team_initials(urls):
    r"""
        Takes team URLS and changes them to {initial : team_url}
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


QUES_REGEX = re.compile(r"^(.*?)(\sQ)?$")
NAME_LINK_REGEX = re.compile(r"^.*?/name/(\w+)/(.*?)$", re.IGNORECASE)
REGULAR_SESSION_REGEX = re.compile(r"^\d{4}\sRegular.*?$")
PLAYER_LINK_REGEX = re.compile(
    r"^.*/player/.*?\d+/([a-zA-Z]+)-([a-zA-Z]+[-]?[a-zA-Z]*).*?$")
SPREAD_REGEX = re.compile(r"^([\-\+]{1}[\d]+\.?[5]?).*?$")
DK_NAME_REGEX = re.compile(r"^(.*?)[(]\w+[)]$")
TOTAL_REGEX = re.compile(r".*?\s([\d]+.*?)")
RANKING_FOR_POS_REGEX = {
    "qb": re.compile(r"addpointer\smyrow\srow_qb.*?"),
    "rb": re.compile(r"addpointer\smyrow\srow_rb.*?"),
    "wr": re.compile(r"addpointer\smyrow\srow_wr.*?"),
    "te": re.compile(r"addpointer\smyrow\srow_te.*?")
}
ESPN_GL_YEAR_REGEX = re.compile(r"^(.*?/id/[\d]+/).*?$")

LAST_YEAR = '2021'
CURRENT_YEAR = '2022'
# Only matters for non current years
GAMELOG_YEAR_URI = "type/nfl/year/" + LAST_YEAR

# https://www.espn.com/nfl/team/stats/_/name/mia/miami-dolphins
# https://www.espn.com/nfl/team/depth/_/name/mia/miami-dolphins
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

DRIVER.set_page_load_timeout(35)
MAX_RETRIES = 3


#
# HTTP Functions
#
def scrape(url):
    r"""
        Rotates IP and user agent for request
    """
    for _ in range(3):
        try:
            headers = {"User-Agent": USER_AGENTS[random.randint(0, 2)]}
            resp = requests.get(url,
                                headers=headers,
                                timeout=20,
                                proxies=PROXIES)
            if resp.status_code == 200:
                return resp
            print("Retrying..")
        except (requests.exceptions.SSLError, requests.exceptions.ProxyError,
                ConnectionError, HTTPError, ConnectTimeout, ReadTimeout):
            print("Failed to get request.. retrying")
    raise Exception("Failed to get: " + url)


def scrape_prop_page(url):
    r"""
        Get page text using Selenium
        Waits for object on prop page before returing
    """
    print("Getting: " + url)
    for _ in range(3):
        try:
            DRIVER.get(url)
            WebDriverWait(DRIVER, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,
                     ".sportsbook-responsive-card-container__body")))
            return DRIVER.page_source
        except Exception as err:
            print(f"Failed due to exception.. retying {err}")
    raise Exception("Failed to get: " + url)


def scrape_js_page(url):
    r"""
        Get page text using Selenium
    """
    for _ in range(3):
        try:
            print("Getting: " + url)
            DRIVER.get(url)
            return DRIVER.page_source
        except Exception as err:
            print(f"Retrying due to error: {err}")
    raise Exception("Failed to get: " + url)


#
# ESPN Scraping
#
# Get links for players in player_names
def get_player_gamelog_links(team_page, player_names):
    r"""
    Gets ESPN links for players passed in player_names
    :param player_names list of players that should be grabbed from ESPN
    :param team_page html for ESPN team page, from requests
    returns {name: link}
    """
    name_link = {}
    for link in BeautifulSoup(team_page.text,
                              "html.parser",
                              parse_only=SoupStrainer("a")):
        if not link.has_attr("href"):
            continue
        # Group 1 = First Name, Group 2 = Last Name
        match = PLAYER_LINK_REGEX.match(link["href"])
        if match is not None:
            # Get N. Harris
            name = (match.group(1).strip()[0:1].upper() + ". " +
                    match.group(2).strip().capitalize())
            if name not in player_names:
                # Should skip players we didn't ask for
                continue
            if name not in name_link:
                link = match.group(0)
                name_link[name] = (link[:link.index("_") - 1] + "/gamelog" +
                                   link[link.index("_") - 1:])
    return name_link


def parse_gamelog_tbody(tbody):
    r"""
    :param tbody is beatiful soup object of table body
    Each sub-list (row) in the list is a game log
    [['10', '12', '12'], ['13','13','43]]
    """
    stats = []
    for row in tbody.findChildren("tr"):
        row_data = []
        for t_data in row.findChildren("td"):
            # Skips rows that are saying this person previously played @ xyz
            if t_data.text.find("Previously") == -1:
                row_data.append(t_data.text)
        if len(row_data) >= 1:
            stats.append(row_data)
    return stats


def parse_table_head(thead):
    r"""
    Creates a ordered dictionary with \{section : \[headers\]\}
    Uses colspan html attribute to decide how many headers to put in
    each section

    :param thead is BeatifulSoup Object of table header

    This is used with the list created in parse_gamelog_tbody to create
    dict of 'stat_name': stat
    """
    section_stats_header = OrderedDict()
    rows = thead.findChildren("tr")
    sections = rows[0].findChildren("th")
    stat_names = [x.text for x in rows[1].findChildren("th")]
    curr_col = 0
    for section in sections:
        colspan = int(section["colspan"])
        section_stats_header[
            section.text.strip()] = stat_names[curr_col:curr_col + colspan]
        curr_col += colspan
    return section_stats_header


def convert_player_name_to_espn(line):
    """
        Convert DK name to ESPN
        T. Name
    """
    name_split = line.split(",")[0].strip()
    return name_split[0:1].upper() + ". " + name_split.split()[1].capitalize(
    ).strip()


def is_regular_season_header(table):
    r"""
        Checks if ESPN table header has correct attributes vs
        the post season table.
    """
    if all(x in table["class"]
           for x in ["Table__header-group", "Table__THEAD"]):
        row = table.find('tr')
        table_header = row.find("th", {"class": ["Table__TH"]})
        if REGULAR_SESSION_REGEX.match(table_header.text):
            return True
    return False


def filter_player_by_depth(team_initial, player_names):
    """
        :returns list of filtered player_names with only starters
        Gets depth chart url using team_initial
    """
    filtered_names = []
    # Replaces stats wtih depth.
    depth_link = re.sub("stats", "depth",
                        INT_TEAM_URL.get(team_initial.upper(), 1))
    soup = BeautifulSoup(scrape(depth_link), "html.parser")
    pos_table = soup.find(
        "table", {"class": ["Table", "Table--fixed", "Table--fixed-left"]})
    pos_rows = list(
        filter(None, [
            x.text.strip() for x in pos_table.find_all(
                "tr", {"class": ["Table__TR", "Table__TR--sm", "Table__even"]})
        ]))
    player_table = soup.find_all("tbody", {"class": ["Table__TBODY"]})[1]
    for (pos, row) in zip(pos_rows, player_table.find_all('tr')):
        amount = 1
        if pos == 'QB':
            # Will only have prop for whoever is starting
            amount = 2
        count = 1
        for table_data in row.find_all('td'):
            if count > amount:
                break
            match = QUES_REGEX.match(table_data.text.strip())
            espn_name = convert_player_name_to_espn(match.group(1))
            if espn_name in player_names:
                filtered_names.append(espn_name)
            count += 1
    return filtered_names


def get_player_gamelogs(team_initial, player_name):
    """
        Gets gamelog stats for a single player and team
    """
    team_url = INT_TEAM_URL.get(team_initial.upper())
    # has names
    link = get_player_gamelog_links(scrape(team_url), [player_name])
    player_stats = {}
    print(f"Processing player: {player_name}")
    gamelogs = {}
    curr_year_link = link.get(player_name)
    last_years_link = ESPN_GL_YEAR_REGEX.match(curr_year_link).group(
        1) + GAMELOG_YEAR_URI

    add_gamelog(curr_year_link, CURRENT_YEAR, gamelogs, player_name)
    add_gamelog(last_years_link, LAST_YEAR, gamelogs, player_name)
    player_stats[player_name] = gamelogs
    return player_stats


def get_players_gamelogs(team_initial, player_names):
    r"""
        Iterates over player_names to get Urls for game logs..
        Gets gamelog for players from ESPN, return {player_name: stats}
    """
    team_url = INT_TEAM_URL.get(team_initial.upper())
    # Filter players down to starts
    player_names = filter_player_by_depth(team_initial.upper(), player_names)
    if team_initial == 'TNF':
        return None
    # has names
    links = get_player_gamelog_links(scrape(team_url), player_names)
    player_stats = {}
    print(f"Processing team: {team_initial}")
    for player_name in links:
        gamelogs = {}
        curr_year_link = links.get(player_name)
        last_years_link = ESPN_GL_YEAR_REGEX.match(curr_year_link).group(
            1) + GAMELOG_YEAR_URI

        add_gamelog(curr_year_link, CURRENT_YEAR, gamelogs, player_name)
        add_gamelog(last_years_link, LAST_YEAR, gamelogs, player_name)
        print(f"Got player: {player_name}")
        player_stats[player_name] = gamelogs
    return player_stats


def add_gamelog(link, year, gamelogs, player_name):
    """
        Gets gamelog for 'year' and adds it to 'gamelogs'
        Used in: get_player_gamelog_per_team
    """
    gamelog = parse_player_gamelog(scrape(link))
    if gamelog is not None:
        gamelogs[year] = gamelog
    else:
        print(f"Can't get {player_name} stats from {year}")


def parse_player_gamelog(http_resp):
    r"""
        :param http_resp is a requests response from the ESPN page
        Parse stats from gamelog html
        Returns list of game log dictionarys.. [{'yds': 10, ...}]
    """
    soup = BeautifulSoup(http_resp.text, "html.parser")

    section_stats_header = None
    for thead in soup.find_all(lambda tag: tag.name == "thead"):
        if is_regular_season_header(thead):
            section_stats_header = parse_table_head(thead)
    if section_stats_header is None:
        return None

    all_tables = soup.find_all(lambda tag: tag.name == "tbody")
    if len(all_tables) > 2:
        stats = parse_gamelog_tbody(all_tables[1])
    else:
        stats = parse_gamelog_tbody(all_tables[0])
    # Combine stats and header using the colspan html attribute.
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


#
# DK Functions
#
def is_prop_link(link):
    """
        :param soup <a> tag this function checks html classes
        Makes sure link from draft kings has the correct attributes
    """
    if link.get('class') is None or len(link.get('class')) == 0:
        return False
    if link['class'][0].lower() == 'sportsbook-tabbed-subheader__tab-link':
        return True
    return False


def dk_team_to_int(team_name):
    """
        :param full name of player -> middle initial last name
        Takes DK team name and converts to match ESPN
    """
    if team_name in DK_TO_ESPN_NAME_CONV:
        return DK_TO_ESPN_NAME_CONV.get(team_name)
    return team_name.split()[0].strip()


def parse_team_name(prop_page):
    """
        :prop_page html from a selenium get
        Parses DK team name out of page title and converts to match ESPN
        the team name is not on live pages..
    """
    soup = BeautifulSoup(prop_page, "html.parser")
    teams = re.sub("AT", "@", [
        div.text for div in soup.find_all(
            "div", {"class": {"event-page-countdown-timer__title"}})
    ][0], 1).split("@")
    return dk_team_to_int(teams[0]) + " @ " + dk_team_to_int(teams[1])


def parse_dk_game_page(game_page):
    """
        :param game_page is the soup of DK's page for an NFL game
        Takes DK game page source, and returns {CHI @ WSH: [passing source, rec/rushing source]}
    """
    pages = []
    for game_link in game_page.findAll('a', href=True):
        if is_prop_link(game_link):
            if game_link['href'].find(PASSING_PROP_URI) != -1 or game_link[
                    'href'].find(RUSH_AND_REC_PROP_URI) != -1:
                source = scrape_prop_page(DK_BASE_PAGE_URL + game_link['href'])
                pages.append(source)
    return {parse_team_name(pages[0]): pages}


def parse_game_spread(game_page):
    """
        :param game_page is soup of an DK NFL game page
        Takes DK game page source, and return {Spread: {CHI: "+4", "WSH -4}}
    """

    spread_table = game_page.find("tbody",
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


def parse_game_total(game_page):
    """
        :param game_page is soup of an NFL DK game page
        Returns {"Total": total}
    """
    total_table = game_page.find("tbody",
                                 {"class": ["sportsbook-table__body"]})
    t_row = total_table.find('tr')
    tds = t_row.findAll("td", {"class": ["sportsbook-table__column-row"]})
    total = TOTAL_REGEX.match(tds[1].text).group(1)
    return {"Total": total}


def get_game_info_from_dk(table_num):
    r"""
        Takes, table_num as in which section to grab from main NFL page
        Get Prop bets that DK has posted

        return [{CHI @ WSH: [prop_page_source, prop_page_source]},
                {Spread: {CHI: "+4", "WSH": "-4"}}, {Total: "45"}}]
    """
    start_time = int(time.time())
    scraped_pages = []
    soup = BeautifulSoup(scrape_js_page(DK_NFL_PAGE_URL), "html.parser")
    table_links = soup.find_all(
        lambda tag: tag.name == "table")[table_num].findAll('a', href=True)
    total_pages = []
    for game_link in table_links:
        if game_link['href'].find("sgp") != -1:
            continue
        next_link = DK_BASE_PAGE_URL + game_link['href']
        if next_link in scraped_pages:
            continue
        scraped_pages.append(next_link)
        soup = BeautifulSoup(scrape_js_page(next_link), "html.parser")
        total_pages.append([
            parse_dk_game_page(soup),
            parse_game_spread(soup),
            parse_game_total(soup)
        ])
    print(
        f"Took: {str(int(time.time()) - start_time)} seconds to retrieve DK pages"
    )
    return total_pages


def fix_odds(text):
    """
        :param text is text from DK odds section
        Turns odds into o32, +200
    """
    seperator = ""
    if text.find('+') != -1:
        seperator = "+"
    else:
        seperator = "−"
    text = re.sub(r'O\s', 'o', text)
    text = re.sub(r'U\s', 'u', text)
    sections = text.split(seperator)
    return sections[0] + " " + seperator + sections[1]


def find_players_team(team_pages, player_name):
    """
        :param team_pages {'url': page source from requests}
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


def parse_dk_prop_pages(dk_prop_dict):
    """
        :param dk_prop_dict {game_name: [passing source, rush/rec source]}
        Extract Prop bets from DK pass Prop section
    """
    game = next(iter(dk_prop_dict))
    team_pages = {}
    teams = [x.strip() for x in game.split('@')]
    for url in [INT_TEAM_URL[x] for x in teams]:
        team_pages[url] = scrape(url).text
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
                data = [
                    player_name,
                    find_players_team(team_pages, player_name), title.text
                ]
                for t_data in row.findAll('td'):
                    if t_data.text.find("O") != -1:
                        data.append(fix_odds(t_data.text))
                props.append(data)
    return props


def get_pos_defense_ranking(class_regex):
    """
        :param class_regex is a regular expression that will match on
        what class you are looking for
        Gets ranking of teams by poistion, grabs information from draft edge
    """
    resp = scrape(DRAFT_EDGE_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.find('tbody').find_all("tr", {"class": class_regex})
    defense_rank = {}
    for row in rows:
        tds = row.find_all('td')
        defense_rank[DRAFT_EDGE_TO_INT.get(tds[0].text.strip())] = float(
            tds[2].text)
    return defense_rank


def get_top_n_def_for_pos(defense_stats, num, worst):
    r"""
        :param defense_stats is dict {team: rank}
        :param num is how many
        :param worst is a boolean to decide sort order before grabbing
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
