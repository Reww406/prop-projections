import pytest
import re

spread_regex = re.compile(r"^([\-\+]{1}[\d]+\.?[5]?).*?$")


class TestsStatsModule:
    """_summary_
    """

    def test_2021_game_year(self):
        """Used for adhoc testing Regular Expressions
        """

        espn_game_log_regex = re.compile(r"^(.*?/id/[\d]+/).*?$")

        print(
            espn_game_log_regex.match(
                "https://www.espn.com/nfl/player/gamelog/_/id/4241479/tua-tagovailoa"
            ).group(1) + "type/nfl/year/2021")