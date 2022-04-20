# (c) 2022 Warren Usui
# Rotisserie league code
# This code is licensed under the MIT license (see LICENSE.txt for details)
"""
get_daily_roto_scores --  Get scores for roto teams on this day.
"""
import os
import json
from get_roto_teams import get_weekly_league_file

def get_daily_roto_scores(rday):
    """
    Create an rteams_on_<date>.json file which contains links to a players
    stats for that day

    @param rday datetime day we are getting the scores for
    """
    lfile = get_weekly_league_file(rday)
    txt_rday = rday.strftime("%Y%m%d")
    update_file = os.sep.join(["data", f"rteams_on_{txt_rday}.json"])
    if os.path.exists(update_file):
        return
    with open(lfile, "r", encoding="utf8") as ofile:
        rleague = json.load(ofile)
    day_data = os.sep.join(["data", f"stats_on_{txt_rday}.json"])
    with open(day_data, "r", encoding="utf8") as ofile:
        precords = json.load(ofile)
    for rteam in rleague:
        for ptype in ['batters', 'pitchers']:
            for pkey in rleague[rteam][ptype]:
                if pkey in precords:
                    rleague[rteam][ptype][pkey]['day_stats'] = precords[pkey]
                else:
                    rleague[rteam][ptype][pkey]['day_stats'] = ""
    with open(update_file, "w", encoding="utf8") as ufile:
        json.dump(rleague, ufile, indent=4)
