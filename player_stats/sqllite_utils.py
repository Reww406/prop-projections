import sqlite3
import re
import datetime

from player_stats import constants as const

RECEIVING_TABLE = """CREATE TABLE IF NOT EXISTS player_rec_gl (
  player_name TEXT NOT NULL,
  season_year INTEGER NOT NULL,
  game_date TEXT NOT NULL,
  team_int TEXT NOT NULL,
  result TEXT NOT NULL,
  opp TEXT NOT NULL,
  rec INTEGER NOT NULL,
  tgts INTEGER NOT NULL,
  yds REAL NOT NULL,
  avg REAL NOT NULL,
  td INTEGER NOT NULL,
  lng REAL NOT NULL,
  UNIQUE(player_name, season_year, game_date) on CONFLICT REPLACE
);"""

RUSH_TABLE = """CREATE TABLE IF NOT EXISTS player_rush_gl (
  player_name text NOT NULL,
  season_year INTEGER NOT NULL,
  game_date TEXT NOT NULL,
  team_int TEXT NOT NULL,
  result TEXT NOT NULL,
  opp TEXT NOT NULL,
  att INTEGER NOT NULL,
  yds REAL NOT NULL,
  avg REAL NOT NULL,
  td INTEGER NOT NULL,
  lng REAL NOT NULL,
  UNIQUE(player_name, season_year, game_date) on CONFLICT REPLACE
);
"""

PASS_TABLE = """
CREATE TABLE IF NOT EXISTS player_pass_gl (
  player_name TEXT NOT NULL,
  season_year INTEGER NOT NULL,
  game_date TEXT NOT NULL,
  team_int TEXT NOT NULL,
  result TEXT NOT NULL,
  opp TEXT NOT NULL,
  cmp INTEGER NOT NULL,
  att INTEGER NOT NULL,
  yds REAL NOT NULL,
  td INTEGER NOT NULL,
  lng REAL NOT NULL,
  inter INTEGER NOT NULL,
  sack INTEGER NOT NULL,
  rtg REAL NOT NULL,
  qbr REAL NOT NULL,
  UNIQUE(player_name, season_year, game_date) on CONFLICT REPLACE
);
"""


# returns row as dictionary
def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_db_in_mem():
    source = sqlite3.connect('nfl_stats.db', check_same_thread=False)
    dest = sqlite3.connect(':memory:', check_same_thread=False)
    source.backup(dest)
    source.close()
    dest.row_factory = _dict_factory
    return dest.cursor()


def get_conn():
    connection = sqlite3.connect('nfl_stats.db', check_same_thread=False)
    connection.row_factory = _dict_factory
    return connection.cursor()


# cur.execute(PASS_TABLE)
# cur.execute(RUSH_TABLE)
# cur.execute(RECEIVING_TABLE)

SEASON_YEAR_REGEX = re.compile(r"(\d){4}.*?")
MONTH_DATE_REGEX = re.compile(r".*?(\d)+[/](\d)+")


def insert_game_logs(gamelogs, player_name, team_init, cur):
    """
      Inserts player game log into SQLite3 Database.
    """
    for log in gamelogs:
        season_key = ""
        season_year = 0
        if log.get(const.CURR_SEASON) is not None:
            season_key = const.CURR_SEASON
            season_year = const.CURRENT_YEAR
        elif log.get(const.LAST_SEASON) is not None:
            season_key = const.LAST_SEASON
            season_year = const.LAST_YEAR
        else:
            raise Exception(
                f"Player: {player_name} gamelog is not this or last years season."
            )

        season_sec = log.get(season_key)
        # date_match = MONTH_DATE_REGEX.match(season_sec.get('Date'))
        # month = int(date_match.group(1))
        # day = int(date_match.group(2))
        date = season_sec.get('Date')
        opp = season_sec.get('OPP')
        result = season_sec.get('Result')
        # epoch = datetime.datetime(int(season_year), month, day).timestamp()

        if log.get(const.PASSING_KEY) is not None:
            _insert_pass_gl(player_name, season_year, date, team_init, result,
                            opp, log.get(const.PASSING_KEY), cur)
        if log.get(const.RUSHING_KEY) is not None:
            _insert_rush_gl(player_name, season_year, date, team_init, result,
                            opp, log.get(const.RUSHING_KEY), cur)
        if log.get(const.RECEIVING_KEY) is not None:
            _insert_rec_gl(player_name, season_year, date, team_init, result,
                           opp, log.get(const.RECEIVING_KEY), cur)


def _insert_pass_gl(player_name, season_year, game_date, team_int, result, opp,
                    log_section, cur):
    cur.execute(
        """INSERT INTO player_pass_gl (player_name, season_year, game_date, team_int, result, opp,
              cmp, att, yds, td, lng, inter, sack, rtg, qbr)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (player_name, season_year, game_date, team_int, result, opp,
         log_section.get('CMP'), log_section.get('ATT'),
         log_section.get('YDS'), log_section.get('TD'), log_section.get('LNG'),
         log_section.get('INT'), log_section.get('SACK'),
         log_section.get('RTG'), log_section.get('QBR')))
    cur.connection.commit()


def _insert_rush_gl(player_name, season_year, game_date, team_int, result, opp,
                    log_section, cur):
    cur.execute(
        """INSERT INTO player_rush_gl (player_name, season_year, game_date, team_int, result, opp,
          att, yds, avg, td, lng)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (player_name, season_year, game_date, team_int, result, opp,
         log_section.get('ATT'),
         log_section.get('YDS'), log_section.get('AVG'), log_section.get('TD'),
         log_section.get('LNG')))
    cur.connection.commit()


def _insert_rec_gl(player_name, season_year, game_date, team_int, result, opp,
                   log_section, cur):
    cur.execute(
        """INSERT INTO player_rec_gl (player_name, season_year, game_date, team_int, result, opp,
          rec, tgts, yds, avg, td, lng)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (player_name, season_year, game_date, team_int, result, opp,
         log_section.get('REC'), log_section.get('TGTS'),
         log_section.get('YDS'), log_section.get('AVG'), log_section.get('TD'),
         log_section.get('LNG')))
    cur.connection.commit()


def get_player_stats_sec(player_name, team_initial, sec, cur):
    """
      Get's all game logs for player and section
    """
    select_statement = f"""
      SELECT * FROM {const.SECTION_FOR_TABLE.get(sec)} WHERE player_name = ? and team_int = ?
    """

    return cur.execute(select_statement,
                       (player_name, team_initial)).fetchall()


def get_game_stats(player_name, team_initial, game_date, sec, cur):
    """
      Get's all game logs for player and section
    """
    select_statement = f"""
      SELECT * FROM {sec} WHERE player_name = ? and team_int = ? and game_date = ?
    """
    return cur.execute(select_statement,
                       (player_name, team_initial, game_date)).fetchone()
