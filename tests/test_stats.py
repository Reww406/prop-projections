import pytest
from player_stats import stats
from player_stats import scraper

PLAYER_STATS = [{
    'YDS': '10'
}, {
    'YDS': '30'
}, {
    'YDS': '32'
}, {
    'YDS': '40'
}, {
    'YDS': '32'
}, {
    'YDS': '45'
}, {
    'YDS': '90'
}]


class TestsStatsModule:
    """_summary_
    """

    def test_remove_outliers(self):
        """_summary_
        """
        scraper.driver_quit()
        print(stats.remove_outliers('YDS', PLAYER_STATS))

    def test_per_of_proj(self):
        """_summary_
        """
        scraper.driver_quit()
        assert stats.per_of_proj(10, 100) == 10

    def test_get_weight_for_spread(self):
        """_summary_
        """
        scraper.driver_quit()
        high_pos = 7
        high_neg_spread = -9
        normal_spread = 4
        print(stats.get_weight_for_spread(high_pos, [-10, 50, 50], 100))
        print(stats.get_weight_for_spread(high_neg_spread, [50, 10, 40], 100))
        print(stats.get_weight_for_spread(normal_spread, [40, 30, -10], 100))

    def test_get_weight_for_def(self):
        """_summary_
        """
        scraper.driver_quit()
        print(stats.get_weight_for_def(100, 'TB', ['TB'], ['BAL'], 10))
        print(stats.get_weight_for_def(100, 'TB', ['BAL'], ['TB'], 10))
