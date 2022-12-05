import sqlite3
import re
import datetime
import pandas as pd

from player_stats import constants as const


# returns row as dictionary
def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_db_in_mem():
    """
        Loads SQLlite3 DB into memory only good for reading
    """
    source = sqlite3.connect('nfl_stats.db', check_same_thread=False)
    dest = sqlite3.connect(':memory:', check_same_thread=False)
    source.backup(dest)
    source.close()
    dest.row_factory = _dict_factory
    return dest.cursor()


def get_conn():
    """
        Opens SQLite3 file.
    """
    connection = sqlite3.connect('nfl_stats.db', check_same_thread=False)
    connection.row_factory = _dict_factory
    return connection.cursor()


SEASON_YEAR_REGEX = re.compile(r"(\d){4}.*?")
MONTH_DATE_REGEX = re.compile(r".*?(\d)+[/](\d)+")


def insert_game_logs(gamelogs, player_name, team_init, cur):
    """
      Inserts player game log into SQLite3 Database.
    """
    for log in gamelogs:
        season_key = ""
        season_year = 0
        if log.get(const.SEASON_2022) is not None:
            season_key = const.SEASON_2022
            season_year = '2022'
        elif log.get(const.SEASON_2021) is not None:
            season_key = const.SEASON_2021
            season_year = '2021'
        elif log.get(const.SEASON_2020) is not None:
            season_key = const.SEASON_2020
            season_year = "2020"
        elif log.get(const.SEASON_2019) is not None:
            season_key = const.SEASON_2019
            season_year = "2019"
        else:
            raise Exception(
                f"Player: {player_name} gamelog is not this or last years season."
            )

        season_sec = log.get(season_key)
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
        """INSERT or IGNORE INTO player_pass_gl (player_name, season_year, game_date,
           team_int, result, opp, cmp, att, yds, td, lng, inter, sack, rtg, qbr)
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
        """INSERT or IGNORE INTO player_rush_gl (player_name, season_year, game_date, 
           team_int, result, opp, att, yds, avg, td, lng)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (player_name, season_year, game_date, team_int, result, opp,
         log_section.get('ATT'),
         log_section.get('YDS'), log_section.get('AVG'), log_section.get('TD'),
         log_section.get('LNG')))
    cur.connection.commit()


def _insert_rec_gl(player_name, season_year, game_date, team_int, result, opp,
                   log_section, cur):
    cur.execute(
        """INSERT or IGNORE INTO player_rec_gl (player_name, season_year, game_date,
           team_int, result, opp, rec, tgts, yds, avg, td, lng)
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


def get_all_game_logs(sec, cur):
    """
      Get's all game logs for player and section
    """
    select_statement = f"""
      SELECT * FROM {const.SECTION_FOR_TABLE.get(sec)}
    """

    return cur.execute(select_statement).fetchall()


def get_game_stats(player_name, team_initial, game_date, sec, cur):
    """
      Get's all game logs for player and section
    """
    select_statement = f"""
      SELECT * FROM {sec} WHERE player_name = ? and team_int = ? and game_date = ?
    """
    return cur.execute(select_statement,
                       (player_name, team_initial, game_date)).fetchone()


def insert_historical_odds(season_year, game_date, team_int, total, spread,
                           cur):
    cur.execute(
        """INSERT INTO odds_archive (season_year, game_date, team_int, total, spread)
        VALUES (?, ?, ?, ?, ?)""",
        (season_year, game_date, team_int, total, spread))
    cur.connection.commit()


def get_odds_for_game(season_year, game_date, team_int, cur):
    """
      Get's odds for game
    """
    select_statement = """
      SELECT * FROM odds_archive WHERE season_year = ? and team_int = ? and game_date = ?
    """
    return cur.execute(select_statement,
                       (season_year, team_int, game_date)).fetchone()
