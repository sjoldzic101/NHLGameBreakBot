import discord, json, traceback
import nhl_gamebreak_lib as nhlgb
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen  # Python 3
from bs4 import BeautifulSoup
from backports.datetime_fromisoformat import MonkeyPatch
from time import gmtime, strftime

def parse_data_from_server(url, auth_ticket="4dM1QOOKk-PQTSZxW_zfXnOgbh80dOGK6eUb_MaSl7nUN0_k4LxLMvZyeaYGXQuLyWBOQhY8Q65k6_uwMu6oojuO"):
    req = Request(url, headers={'Authorization': 'ticket="{}"'.format(auth_ticket)})
    #print('ticket="{}"'.format(auth_ticket))
    #req.add_header('Referrer', 'https://www.premierhockeyfederation.com')
    #req.add_header('Origin', 'https://www.premierhockeyfederation.com')
    #print(req)
    return BeautifulSoup(json.loads(urlopen(req).read())["content"], features="html.parser")

def get_period_ordinal_string(period = "1"):
    suffix = ""
    if period == "1":
        suffix = "st"
    if period == "2":
        suffix = "nd"
    elif period == "3":
        suffix = "rd"

    return (period + suffix)

def get_schedule(date = "today", schedule_url = "https://web.api.digitalshift.ca/partials/stats/schedule/table?division_id=13893&all=true", gameid = "all"):
    schedule = []
    schedule_html_data = parse_data_from_server(url = schedule_url)
    schedule_table = json.loads(schedule_html_data.find_all("div", attrs={'class': 'table-fixed'})[0].find_all("table", attrs={'class': 'schedule'})[0].tbody['ng-init'].split('=')[1])

    if not gameid == "all":
        check_game_id = int(gameid)
        for game in schedule_table:
            game_id = int(game["id"].split("-")[1])

            if game_id == check_game_id:
                schedule.append(game)
    elif date == "all_season":
        for game in schedule_table:
            schedule.append(game)
    else:
        date_to_check = datetime.today()
        time_delta = 0

        if not date == "today":
            if date == "tomorrow":
                time_delta = 1
            elif date == "yesterday":
                time_delta = -1

        date_to_check = (date_to_check + timedelta(days=time_delta)).date()

        for game in schedule_table:
            game_start_date = datetime.fromisoformat(game["datetime"]).date()
            
            if date_to_check == game_start_date:
                schedule.append(game)

    return schedule

def get_nwhl_game_data(boxscore_url = "https://web.api.digitalshift.ca/partials/stats/game/boxscore?game_id=", game_url = "https://web.api.digitalshift.ca/partials/stats/game?game_id=", game="0"):
    game_result = {}

    # https://web.api.digitalshift.ca/partials/stats/game?game_id=368724
    parsed_html_data = parse_data_from_server(boxscore_url + str(game))

#    print(parsed_html_data)
#    exit(0)

    table_col = parsed_html_data.find_all("div", attrs={'class': 'col'})[0].tbody
    scoring_sum_col = parsed_html_data.find_all("div", attrs={'class': 'table-fixed'})[0].tbody.find_all("tr")

    away_team_table = table_col.find_all("tr")[0]
    home_team_table = table_col.find_all("tr")[1]

    away_team_name = away_team_table.find_all("td")[0].text
    away_team_abbr = nhlgb.get_abbr(away_team_name, league = "phf")
    away_team_score = away_team_table.find_all("td")[4].text


    home_team_name = home_team_table.find_all("td")[0].text
    home_team_abbr = nhlgb.get_abbr(home_team_name, league = "phf")
    home_team_score = home_team_table.find_all("td")[4].text

    goal_arr = []
    for goal_val in scoring_sum_col:
        if goal_val.find("td", attrs={'class': 'center'}):
            goal_arr.append(goal_val)

    goal = goal_arr[-1]

    try:
        period = goal.find_all("td", attrs={'class': 'center'})[0].text
        strength = goal.find_all("td", attrs={'class': 'center'})[2].text.lstrip().rstrip()
        scorers = goal.find_all("td")[4].find_all("a", attrs={'class': 'person-inline'})
    except Exception as e:
        period = "N/A"
        time = "N/A"
        strength = "N/A"
        scorers = []

    goal_scorer = "Unknown"
    primary_assister = "unassisted"
    secondary_assister = ""

    if len(scorers) > 0:
        goal_scorer = goal.find_all("a", attrs={'class': 'person-inline'})[0].text

        if len(scorers) > 1:
            primary_assister = goal.find_all("a", attrs={'class': 'person-inline'})[1].text

            if len(scorers) > 2:
                secondary_assister = goal.find_all("a", attrs={'class': 'person-inline'})[2].text

    game_name = away_team_abbr + "at" + home_team_abbr
    game_result[game_name] = {}

    game_result[game_name]["game_score"] = {}
    game_result[game_name]["latest_goal"] = {}
    game_result[game_name]["latest_goal"]["goal_scorer"] = goal_scorer
    game_result[game_name]["latest_goal"]["assisted_by"] = primary_assister

    if not secondary_assister == "":
        game_result[game_name]["latest_goal"]["assisted_by"] = game_result[game_name]["latest_goal"]["assisted_by"] + ", " + secondary_assister

    game_result[game_name]["latest_goal"]["goal_type"] = {}

    game_result[game_name]["latest_goal"]["goal_type"]["powerplay"] = False
    game_result[game_name]["latest_goal"]["goal_type"]["shorthanded"] = False
    game_result[game_name]["latest_goal"]["goal_type"]["empty_net"] = False

    if strength == "PP":
        game_result[game_name]["latest_goal"]["goal_type"]["powerplay"] = True
    elif strength == "SH":
        game_result[game_name]["latest_goal"]["goal_type"]["shorthanded"] = True

    if "EN" in strength:
        game_result[game_name]["latest_goal"]["goal_type"]["empty_net"] = True

    game_result[game_name]["playoffs"] = False

    parsed_game_html_data = parse_data_from_server(game_url + str(game))
    #print(parsed_game_html_data)

    try:
        game_start_time = str(datetime.strptime(parsed_game_html_data.find_all("header", attrs={'class': 'hero game'})[0]['ng-init'].split('-')[1].lstrip().rstrip("'"), '%B %d, %Y %I:%M%p').replace(tzinfo=None).astimezone(tz=timezone.utc).isoformat()).split('+')[0] + "Z"
    except ValueError:
        game_start_time = "2021-01-01T00:00:00Z"

    timestamp = ""
    state = "Preview"
    state = get_schedule(gameid = game)[0]["status"]
    if state == "Final":
        state = "FINAL"
    elif state == "Not Started":
        state = "Preview"
    else:
        state = "LIVE"

        try:
            game_state = json.loads(parsed_game_html_data.find_all("div", attrs={'class': 'bh-white'})[0].div['data-game-clock'])
        except Exception as e:
            game_state = {}
            game_state["time"] = 1200
            game_state["period"] = "1"
            state = "Preview"

        timestamp = 1200 - int(float(game_state["time"]))
        period = get_period_ordinal_string(game_state["period"])

        if timestamp == 0:
            timestamp = "END " + period
        elif timestamp == 1200 and period == "1st":
            state = "Preview"
        else:
            timestamp = strftime("%M:%S", gmtime(timestamp)) + " " + get_period_ordinal_string(game_state["period"])

    game_result[game_name]["game_score"][away_team_abbr] = int(away_team_score)
    game_result[game_name]["game_score"][home_team_abbr] = int(home_team_score)
    game_result[game_name]["game_score"]["start_time"] = game_start_time
    game_result[game_name]["game_score"]["overtime"] = False
    game_result[game_name]["game_score"]["shootout"] = False
    game_result[game_name]["state"] = state
    game_result[game_name]["league"] = "PHF"
    game_result[game_name]["timestamp"] = timestamp

    return game_result

def get_active_schedule():
    active_schedule = {}
    schedule = get_schedule(date = "today")

    for game in schedule:
        if not game["status"] == "Not Started":
            game_id = int(game["id"].split("-")[1])
            game_data = get_nwhl_game_data(game = game_id)

            game_data_key = "NWHLatNWHL"

            if len(game_data) > 0:
                game_data_key = list(game_data.keys())[0]

            active_schedule.update(game_data)


    return active_schedule

def exec_get_func(url = None):
    MonkeyPatch.patch_fromisoformat()
    return get_active_schedule()
