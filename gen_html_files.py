# (c) 2022 Warren Usui
# Rotisserie league code
# This code is licensed under the MIT license (see LICENSE.txt for details)
"""
generate html files from data/rteams_on_<date>.json files.  Save html pages
in html<date> directory
"""
import os
import json

def gen_html_files(date_info):
    """
    Generate a directory for the date specified.  That directory will
    contain an html file for each roto team that contains that teams stats
    for that day

    @param date_info datetime value
    """
    tempv = date_info.strftime("%Y%m%d")
    ndate = date_info.strftime("%A - %B %d, %Y")
    dirname = f"html_files_{tempv}"
    with open("tablehtml.txt", "r", encoding="utf8") as iofile:
        tpattern = iofile.read()
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    fileio = os.sep.join(["data", f"rteams_on_{tempv}.json"])
    with open(fileio, "r", encoding="utf8") as iofile:
        team_data = json.load(iofile)
    fnames = []
    txtvals = []
    for tempv in team_data:
        fnames.append(
            tempv.replace(" ", "_").replace("&", "X").replace("'", "X")
        )
        txtvals.append(tempv.replace("&", "&amp;").replace("'", "&apos;"))
    print(fnames)
    print(txtvals)
    bheaders = ["NAME", "TEAM", "POSITION", "AT BATS", "AVG", "RUNS",
               "RBIS", "HR", "SB"]
    pheaders = ["NAME", "TEAM", "WIN", "SAVE", "INNINGS",
               "ERA", "WHIP", "K/9"]
    for indx, tempv in enumerate(team_data):
        ltables = []
        ltables.append(get_new_table(team_data[tempv]["batters"],
                               bheaders, bdata_func))
        ltables.append(get_new_table(team_data[tempv]["pitchers"],
                               pheaders, pdata_func))
        otxt = tpattern[:] % (txtvals[indx], txtvals[indx], ndate,
                              ltables[0], ltables[1])
        fileio = os.sep.join([dirname, f"{fnames[indx]}.html"])
        with open(fileio, "w", encoding="utf8") as iofile:
            iofile.write(otxt)

def init_table_header(headers):
    """
    Generate the header for a table

    @param headers List of column headings for this table
    @return html output for the header row of the table as a single element
            in a list
    """
    hcells = []
    for col_txt in headers:
        hcells.append(wrapper(col_txt, "th"))
    header = "".join(hcells)
    wheader = wrapper(header, "tr")
    return [wheader]

def bdata_func(tlines, day_stats):
    """
    Function to add batting statistics for one player to the html table

    @param tlines html file so far.  We add stats to this
    @param day_stats dict of statistics for a player
    """
    if 'save' in day_stats:
        return tlines
    tlines.append(wrapper(str(day_stats['ab']), 'td'))
    atbs =  day_stats['ab']
    if atbs == 0:
        atbs = 1
    bavg = day_stats['hits'] / atbs
    tlines.append(wrapper(format(round(bavg, 3), '.3f').lstrip('0'), 'td'))
    tlines.append(wrapper(str(day_stats['runs']), 'td'))
    tlines.append(wrapper(str(day_stats['rbis']), 'td'))
    tlines.append(wrapper(str(day_stats['hr']), 'td'))
    tlines.append(wrapper(str(day_stats['sb']), 'td'))
    return tlines

def pdata_func(tlines, day_stats):
    """
    Function to add pitching statistics for one player to the html table

    @param tlines html file so far.  We add stats to this
    @param day_stats dict of statistics for a player
    """
    tlines.append(wrapper(str(day_stats['win']), 'td'))
    tlines.append(wrapper(str(day_stats['save']), 'td'))
    outs = day_stats['outs']
    full_inn = outs // 3
    part_inn = outs % 3
    if part_inn == 0:
        inpit = str(full_inn)
    else:
        inpit = str(full_inn) + " " + str(part_inn) + "/3"
    tlines.append(wrapper(inpit, 'td'))
    eruns = day_stats['earned_runs']
    era = 27 * eruns / outs
    erastr = format(round(era, 2), '.2f')
    tlines.append(wrapper(erastr, 'td'))
    wlkhts = day_stats['walks'] + day_stats['hits']
    whip = 3 * wlkhts / outs
    whipstr = format(round(whip, 3), '.3f')
    tlines.append(wrapper(whipstr, 'td'))
    kstr = 27 * day_stats['strikeouts'] / outs
    kstro = format(round(kstr, 3), '.3f')
    tlines.append(wrapper(kstro, 'td'))
    return tlines

def get_new_table(players, headers, data_func):
    """
    Generate a table for the roto team display

    @param players dict of players indexed by Cbs player number
    @param headers list of column headings for the table
    @param data_func stat extraction function (different for batters and
                                               pitchers)
    """
    ttable = init_table_header(headers)
    for number in players:
        tlines = []
        indata = players[number]
        tlines.append(wrapper(indata['name'], 'td align="left"'))
        tlines.append(wrapper(indata['team'], 'td'))
        if not indata['position'] == 'P':
            tlines.append(wrapper(indata['position'], 'td'))
        if indata['day_stats']:
            tlines = data_func(tlines, indata['day_stats'])
        else:
            for _  in range(6):
                tlines.append(wrapper('-', 'td'))
        dline = "".join(tlines)
        dline = wrapper(dline, "tr")
        ttable.append(dline)
    records = "\n".join(ttable)
    return wrapper(records, 'table border="1"')

def wrapper(data, wrap):
    """
    Wrap a data field inside the html element specified

    @param data String data to wrap
    @param wrap String wrapping element name
    @returns <wrap>data</wrap>
    """
    ewrap = wrap.split(" ")[0]
    return f"<{wrap}>{data}</{ewrap}>"
        