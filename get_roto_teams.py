# (c) 2022 Warren Usui
# Rotisserie league code
# This code is licensed under the MIT license (see LICENSE.txt for details)
"""
get_league_team_data creates a json file of all team lineups for the
current period.  File name is league-YYYY-MM-DD.json where the date is
the first day in the period.
"""
import os
import json
from datetime import datetime, timedelta
from configparser import ConfigParser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import chromedriver_autoinstaller
from bs4 import BeautifulSoup

def get_league_team_data(when_to_get):
    """
    Extract the username, password, and league name from the ini.file
    Use username/password combination and league name to create a driver.
    Calls get_all_teams to get the team information.
    Saves the results in a json file whose name is derived from the starting
    date of this scoring period.
    """
    ofilen = get_weekly_league_file(when_to_get)
    if os.path.exists(ofilen):
        return
    config = ConfigParser()
    config.read('roto.ini')
    parse_info = config["DEFAULT"]
    league = parse_info["league"]
    driver = cbs_login(parse_info["username"],
                       parse_info["password"])
    team_data = get_all_teams(driver, league)
    with open(ofilen, "w", encoding="utf8") as data_file:
        json.dump(team_data, data_file, indent=4)
    driver.quit()

def get_weekly_league_file(cdate):
    """
    Get league rosters

    @param cdate date we are interested in.  Get appropriate league file for
           that week.
    @return String name of file containing rosters for the specified week.
    """
    ddiff = cdate.weekday() - 2
    if ddiff < 0:
        ddiff += 7
    newd = cdate - timedelta(days=ddiff)
    sdate = newd.strftime("%Y-%m-%d")
    ofilen = os.sep.join(["data", f"league-{sdate}.json"])
    return ofilen

def wait_get(wtime, driver, locator):
    """
    Wait while selenium displays stuff

    @param wtime integer seconds until timeout if object is not present
    @param driver object Selenium driver
    @param locator tuple Selenium webdriver locator we are waiting for

    @return object Webelement that we are waiting for
    """
    try:
        _ = WebDriverWait(driver, wtime).until(
            EC.presence_of_element_located(locator)
        )
    except TimeoutException:
        print("Aaargh!! Bad News!!")
    return driver.find_element(locator[0], locator[1])

def cbs_login(usern, passw):
    """
    Login in the the Cbs site

    @param usern String my user name
    @param passw String corresponding password
    @return Selenium driver after login
    """
    chromedriver_autoinstaller.install()
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(service=Service(), options=options)
    driver.get('https://www.cbssports.com/user/login/' +
               '?redirectUrl=https%3A%2F%2Fwww.cbssports.com%2F')
    username = wait_get(15, driver, (By.ID, "app_login_username"))
    username.send_keys(usern)
    password = wait_get(15, driver, (By.ID, "app_login_password"))
    password.send_keys(passw)
    button = wait_get(15, driver, (By.CLASS_NAME, "BasicButton"))
    button.click()
    return driver

def get_all_teams(driver, league):
    """
    Loop through all teams in the league and extract the player data

    @param driver Selenium driver
    @param league league name (supplied by Cbssports and stashed in ini file)
    @return dict rosters indexed by team name
    """
    driver.get(f"https://{league}.cbssports.com/standings/overall")
    wpage = driver.page_source.encode("utf-8")
    soup = BeautifulSoup(wpage, "html.parser")
    tm_info = soup.find_all("a", href=True)
    all_rosters = {}
    for tagv in tm_info:
        if 'href' in tagv.attrs:
            if tagv.attrs['href'].startswith('/teams/'):
                keyv, pinfo = get_indv_team(driver, league, tagv)
                all_rosters[keyv] = pinfo
    return all_rosters

def parse_players(pinfo, ret_team):
    """
    Parse the information extracted from the web page for a team and
    find all active and reserved players

    @param pinfo Beautiful Soup object (potential player lines)
    @param ret_team dictionary of players for a team
    @return updated ret_team
    """
    plcount = 14
    batcnt = True
    for entry in pinfo:
        person = entry.find("a", class_="playerLink")
        if not person:
            continue
        pname = person.get_text()
        href = person["href"]
        pnumb = href.split("/")[-1]
        posinfo = entry.find("span",
                             class_='playerPositionAndTeam').get_text()
        posdata = posinfo.strip().split(" | ")
        if posdata[0] == "P" and batcnt:
            batcnt = False
            plcount = 9
        #plcount -= 1
        reserved = False
        if plcount <= 0:
            reserved = True
        plcount -= 1
        newguy = {}
        newguy["position"] = posdata[0]
        newguy["team"] = posdata[1]
        newguy["name"] = pname
        rkey = "batters"
        if posdata[0] == "P":
            rkey = "pitchers"
        if reserved:
            rkey = "reserves"
        ret_team[rkey][pnumb] = newguy
        print(posdata, pnumb, pname, reserved)
    return ret_team

def get_indv_team(driver, league, team):
    """
    Extract roster information for a team

    @param driver object Selenium driver
    @param league String league name (returned from CBS)
    @param team String name of this team
    @retrun tname, ret_team string, dict Rotisserie team name (used as key
                                    in another dict, and dict containing
                                    player information
    """
    tlink = team.attrs['href']
    tname = team.get_text()
    ret_team = {'batters': {}, 'pitchers': {}, 'reserves': {}}
    ret_team['team_name'] = tname
    driver.get(f"https://{league}.cbssports.com{tlink}")
    tpage = driver.page_source.encode("utf-8")
    soup = BeautifulSoup(tpage, "html.parser")
    pinfo = soup.find_all("tr", class_="playerRow")
    print("*** ", tname)
    ret_team = parse_players(pinfo, ret_team)
    return tname, ret_team

if __name__ == "__main__":
    get_league_team_data(datetime.now())
