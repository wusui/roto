# (c) 2022 Warren Usui
# Rotisserie league code
# This code is licensed under the MIT license (see LICENSE.txt for details)
"""
generate free_agent data to be saved in files created by gen_html
"""
import os
import json
from datetime import datetime, timedelta
from get_roto_teams import get_weekly_league_file

def find_unclaimed(cdate):
    """
    Find players who contributed on date specified that are not on the roster
    of any fantasy team in this league

    @param cdate datetime curent date
    @return list of index numbers for free agent players
    """
    retv = []
    taken_file = get_weekly_league_file(cdate)
    with open(taken_file, "r", encoding="utf8") as taken_fd:
        taken_info = json.load(taken_fd)
    for taken_keys in taken_info:
        for ptype in taken_info[taken_keys]:
            if ptype != "team_name":
                for plyr in taken_info[taken_keys][ptype]:
                    retv.append(plyr)
    return retv

def proc_bat(batter):
    """
    Calculate adjusted batting average for this batter

    @param batter dict batter stats
    @return returns batter dict with w_avg stat added
    """
    retv = batter.copy()
    numerator = batter['hits'] + 10
    denominator = batter['ab'] + 40
    retv['w_avg'] = numerator / denominator
    return retv

def proc_pit(pitcher):
    """
    Calculate adjusted era, whip, and ks/9 for this pitcher

    @param pitcher dict pitcher stats
    @return pitcher dict with w_era, w_whip and w_k9 stats added
    """
    retv = pitcher.copy()
    denominator = pitcher['outs'] + 21
    numerator = (pitcher['earned_runs'] + 3) * 27
    retv['w_era'] = numerator /  denominator
    numerator = (pitcher['walks'] + pitcher['hits'] + 9) * 3
    retv['w_whip'] = numerator / denominator
    numerator = (pitcher['strikeouts'] + 6) * 27
    retv['w_k9'] = numerator / denominator
    return retv

def get_free_agents():
    """
    Scan for free agents that participated in games yesterday.

    @return tuple of batter info and pitcher info of contributing free
            agents
    """
    yesterday = datetime.now() - timedelta(days=1)
    active = find_unclaimed(yesterday)
    dpart = yesterday.strftime("%Y%m%d")
    fname = os.sep.join(["data", "".join(["stats_on_", dpart, ".json"])])
    pit_info = {}
    bat_info = {}
    with open(fname, "r", encoding="utf8") as day_fd:
        day_info = json.load(day_fd)
    with open(os.sep.join(["data", "abbreviations.json"]), "r",
                       encoding="utf8") as afile:
        teamabbrv = json.load(afile)
    for plyr_keys in day_info:
        if day_info[plyr_keys]['team'] not in teamabbrv:
            continue
        if plyr_keys not in active:
            if 'save' not in day_info[plyr_keys]:
                bat_info[plyr_keys] = proc_bat(day_info[plyr_keys])
            else:
                pit_info[plyr_keys] = proc_pit(day_info[plyr_keys])
    return get_with_stats(bat_info, pit_info)

def get_with_stats(bat_info, pit_info):
    """
    Add adjusted stats to bat_info and pit_info

    @param bat_info day_info for this batter
    @param pit_info day_info for this pitcher
    @return tuple (bat_info, pit_info) with adjusted stats wrapped inside
                   dict that gen_html_files can handle
    """
    b_return = {}
    for b_keys, batter  in bat_info.items():
        if batter['runs'] + batter['rbis'] + batter['sb'] > 0:
            b_return[b_keys] = day_wrap(batter)
        else:
            if batter['hits'] > 1:
                b_return[b_keys] = day_wrap(batter)
    base_era = 81 / 21
    base_whip = 9 / 7
    base_k9 = 6 * 27 / 21
    p_return = {}
    for p_keys, pitcher in pit_info.items():
        if pitcher['win'] + pitcher['save'] > 0:
            p_return[p_keys] = day_wrap(pitcher)
        else:
            if ((pitcher['w_era'] < base_era) and
                (pitcher['w_whip'] < base_whip) and
                (pitcher['w_k9'] > base_k9)):
                p_return[p_keys] = day_wrap(pitcher)
    return b_return, p_return

def day_wrap(player):
    """
    Wrapper to keep gen_html_files happy

    @param player data (day_stats)
    @param return dictionary entry with day_stats
    """
    fmt_ply = {}
    fmt_ply['name'] = player['name']
    fmt_ply['team'] = player['team']
    fmt_ply['position'] = player['pos']
    fmt_ply['day_stats'] = player
    return fmt_ply
