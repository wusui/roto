# (c) 2022 Warren Usui
# Rotisserie league code
# This code is licensed under the MIT license (see LICENSE.txt for details)
"""
Collect the statistics for all players on a given date.
"""
import os
import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup

def get_players_on(txt_date):
    """
    Get player results for YYYY-mm-dd
    """
    return get_players_on_date(datetime.strptime(txt_date, "%Y-%m-%d"))

def get_games_on_date(game_date):
    """
    Collect links to boxscores for games played on game_date
    """
    with open(os.sep.join(["data", "abbreviations.json"]), "r",
                       encoding="utf8") as afile:
        teamabbrv = json.load(afile)
    gday = game_date.strftime("%Y%m%d")
    url = f"https://www.cbssports.com/mlb/scoreboard/{gday}/"
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    glist = soup.find_all("a", href=True)
    retv = []
    for entry in glist:
        if "boxscore/MLB_" in entry["href"]:
            mlb_teams = entry["href"].split("_")[-1]
            mlb_teams = mlb_teams.strip("_/").split("@")
            if mlb_teams[0] in teamabbrv or mlb_teams[1] in teamabbrv:
                retv.append(entry["href"])
    return retv

def get_players_on_date(game_date):
    """
    Collect the statistics for all players and save that data in a json file
    """
    games_played = get_games_on_date(game_date)
    indx = games_played[0].split("_")[1]
    ofilen = os.sep.join(["data", f"stats_on_{indx}.json"])
    if os.path.exists(ofilen):
        return
    stats_on_this_date = {}
    for boxscore in games_played:
        print(boxscore)
        raw_data = extract_raw_data(boxscore)
        records = process_raw_data(raw_data)
        stats_on_this_date.update(records)
    with open(ofilen, "w", encoding="utf8") as ofile:
        json.dump(stats_on_this_date, ofile, indent=4)

def extract_raw_data(boxscore):
    """
    Scrape data from website for boxscore specified

    @param boxscore String link to box score page
    @returns extracted data, referred to as raw_data in the rest of this
             module
    """
    boxpage = "https://www.cbssports.com" + boxscore
    txt = requests.get(boxpage).content
    soup = BeautifulSoup(txt, "html.parser")
    bs_tables = soup.find_all("table")
    retv = []
    for cnt, tbl in enumerate(bs_tables):
        if cnt > 7:
            break
        if cnt % 2 == 0:
            continue
        retv.append([cnt, boxpage.split("/")[-2]])
        records = tbl.find_all("tr")
        for record in records:
            orec = []
            data = record.find_all("td")
            if data:
                orec.append(data[0].find("a")["href"].split("/")[-3])
                for field in data:
                    orec.append(field.get_text())
                retv.append(orec)
    retv.append(parse_sb_info(soup))
    return retv

def parse_sb_info(soup):
    """
    Extract the box score stolen base data

    @param soup Beautiful Soup object derived from raw text
    @return list of Strings Stolen base data from boxscore
    """
    all_text = soup.get_text("#")
    sbinfo = []
    brunning = all_text.split("BASERUNNING")
    if len(brunning) > 1:
        sbinfo.append("BASERUNNING")
        for indx in range(1, len(brunning)):
            strloc = brunning[indx].find("#SB#")
            if strloc >= 0:
                newstr = brunning[indx][strloc + 4:] + "#"
                nxthash = newstr.find("#")
                sbinfo.append(newstr[0:nxthash])
    return sbinfo

def update_stolen_bases(plyr_data, sbinfo):
    """
    Update stolen base information

    @param plyr_data dict of player information
    @param sbinfo stolen base information extracted from box scores
    @return plyr_data with stolen base stats adjusted
    """
    for entry in sbinfo:
        new_data = entry[3:].split(", ")
        for plyr in new_data:
            aplyr = plyr.split("(")[0].strip()
            parts = aplyr.split(" ")
            count = 1
            if parts[-1].isnumeric():
                count = int(parts[-1])
                aplyr = " ".join(parts[0:-1])
            for entry2 in plyr_data:
                if plyr_data[entry2]['name'] == aplyr:
                    plyr_data[entry2]['sb'] = count
                    break
    return plyr_data

def process_raw_data(raw_data):
    """
    Convert raw data (Fields extracted from web page) into nicely formatted
    dictionary.

    @param raw_data String scraped data from web pages
    @return dict indexed by Cbssports player number of this days stats for
            the corresponding player
    """
    pit_mode = False
    pteam = ""
    plyr_data = {}
    for rline in raw_data:
        if not rline:
            continue
        if rline[0] ==  "BASERUNNING":
            if len(rline) > 1:
                llen = (len(rline) - 1) // 2
                sbinfo = rline[1:(llen + 1)]
                plyr_data = update_stolen_bases(plyr_data, sbinfo)
            continue
        if len(rline) == 2 and rline[1].startswith("MLB"):
            teams = rline[1].split("_")[-1].split("@")
            pit_mode = True
            if rline[0] < 4:
                pit_mode = False
            if rline[0] % 4 == 1:
                pteam = teams[0]
            else:
                pteam = teams[1]
        else:
            player_key = int(rline[0])
            plyr_data[player_key] = make_player_entry(rline, pit_mode, pteam)
    return plyr_data

def make_player_entry(rline, pit_mode, pteam):
    """
    Assemble the actual player data

    @param rline String line from raw_data
    @param pit_mode True if pitcher, false if batter
    @param pteam String MLB team abbreviation
    @return new player entry to be added to dict of stats for this day.
    """
    player_data = {"team": pteam}
    if pit_mode:
        player_data['pos'] = 'P'
        pname_parts = rline[1].split("(")
        player_data['name'] = remove_dash(pname_parts[0].strip())
        player_data['save'] = 0
        player_data['win'] = 0
        if len(pname_parts) > 1:
            if pname_parts[1].startswith("W"):
                player_data['win'] = 1
            if pname_parts[1].startswith("S"):
                player_data['save'] = 1
        inn_inf = rline[2].split(".")
        player_data['outs'] = int(inn_inf[0]) * 3 + int(inn_inf[1])
        player_data['hits'] = int(rline[3])
        player_data['earned_runs'] = int(rline[5])
        player_data['walks'] = int(rline[6])
        player_data['strikeouts'] = int(rline[7])
    else:
        ptext = rline[1].split(" ")
        player_data['name'] = remove_dash(" ".join(ptext[0:-1]))
        player_data['pos'] = ptext[-1]
        player_data['ab'] = int(rline[2])
        player_data['runs'] = int(rline[3])
        player_data['hits'] = int(rline[4])
        player_data['rbis'] = int(rline[5])
        hrval = rline[6]
        if hrval == '-':
            hrval = 0
        player_data['hr'] = hrval
        player_data['sb'] = 0
    return player_data

def remove_dash(pname):
    """
    Remove the dash from sustitution headers of names in box scores

    @param pname String box score text
    @return String updated string
    """
    parts = pname.split(" ")
    if not parts[0].endswith("-"):
        return pname
    return " ".join(parts[1:])

if __name__ == "__main__":
    get_players_on("2022-04-14")
