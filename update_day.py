# Rotisserie league code
# This code is licensed under the MIT license (see LICENSE.txt for details)
"""
Get yesterday's stats for all teams
"""
from datetime import datetime, timedelta
from get_team_abbrev import get_teams_list
from get_roto_teams import get_league_team_data
from get_day_stats import get_players_on_date
from get_daily_roto_scores import get_daily_roto_scores
from gen_html_files import gen_html_files

def complete_yesterday():
    """
    Call get_info_for_day with yesterday's date
    """
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    get_info_for_day(yesterday)

def get_info_for_day(test_day):
    """
    Produce files needed to check results for a day

    @param test_day date value of day being checked
    """
    get_teams_list()
    get_league_team_data(test_day)
    get_players_on_date(test_day)
    get_daily_roto_scores(test_day)
    gen_html_files(test_day)

if __name__ == "__main__":
    complete_yesterday()
