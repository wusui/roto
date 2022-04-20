# (c) 2022 Warren Usui
# Rotisserie league code
# This code is licensed under the MIT license (see LICENSE.txt for details)
"""
get_teams_list -- writes data/abbreviations.json file
"""
import os
import json
import requests
from bs4 import BeautifulSoup

def get_teams_list():
    """
    Place all the team abbreviations into a json file
    (data/abbreviations)
    """
    ofilen = os.sep.join(["data", "abbreviations.json"])
    if os.path.exists(ofilen):
        return
    url_data = requests.get("https://www.cbssports.com/mlb/teams/")
    soup = BeautifulSoup(url_data.content, "html.parser")
    league_blks = soup.find_all("div", class_="TableBaseWrapper")
    for league_chk in league_blks:
        al_ind = league_chk.find_all("span", class_="TeamLogoNameLockup-name")
        if al_ind[0].get_text().strip() == "American League":
            dup_teams = []
            tfields = league_chk.find_all("a", href=True)
            for team_info in tfields:
                dup_teams.append(team_info["href"].split("/")[3])
            answer = list(set(dup_teams))
            with open(ofilen, "w", encoding="utf8") as ofile:
                json.dump(answer, ofile, indent=4)
            break

if __name__ == "__main__":
    get_teams_list()
