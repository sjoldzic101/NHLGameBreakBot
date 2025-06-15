import discord
import urllib.request
import json
from get_scores import get_scores
import nhl_gamebreak_lib as nhlgb
from datetime import date, datetime, timezone
from backports.datetime_fromisoformat import MonkeyPatch

def get_nhlapi_schedule_for_date(url = "https://statsapi.web.nhl.com/api/v1/schedule", for_date = date.today()):
    today_nhlapi_url = url + '?date={:%Y-%m-%d}'.format(for_date)
    today_nhlapi_url = today_nhlapi_url + "&expand=schedule.teams,schedule.linescore,schedule.broadcasts.all"
    nhlapi_data = urllib.request.urlopen(today_nhlapi_url).read().decode()
    return json.loads(nhlapi_data)["dates"][0]["games"]

def get_nhl_schedule(client = discord.Client(), date_to_check = "today"):
    schedule_string = ""
    nhlapi_schedule_dict = {}

    emojis = nhlgb.get_emoji_list(discord_client = client)

    schedule_string = get_scores(client = client, date = date_to_check)

    check_date = nhlgb.get_check_date(date_to_check = date_to_check)

    nhlapi_schedule_dict = get_nhlapi_schedule_for_date(for_date = check_date)

    for nhl_game in nhlapi_schedule_dict:
        if nhl_game["status"]["abstractGameState"] == "Preview":
            away_team = nhlgb.get_abbr(nhl_game["teams"]["away"]["team"]["name"])
            home_team = nhlgb.get_abbr(nhl_game["teams"]["home"]["team"]["name"])

            broadcasts = "TV: N/A"

            if "broadcasts" in nhl_game:
                broadcasts = "TV: "
                for network in nhl_game["broadcasts"]:
                    broadcasts = broadcasts + network["name"] + ", "
                broadcasts = broadcasts[:-2]

            game_start_time = '{:%I:%M %p %Z}'.format(datetime.fromisoformat(nhl_game["gameDate"].replace("Z", "")).replace(tzinfo=timezone.utc).astimezone(tz=None))
            away_team_emoji = nhlgb.get_emoji(away_team, emojis = emojis, league = "nhl")
            home_team_emoji = nhlgb.get_emoji(home_team, emojis = emojis, league = "nhl")

            if nhl_game["status"]["detailedState"] == "Postponed":
                game_start_time = "PPD"
                broadcasts = ""

            schedule_string = schedule_string + away_team_emoji + " " + away_team + " @ " + home_team_emoji + " " + home_team + ", " + game_start_time + ". " + broadcasts + "\n"

    return schedule_string

# Primary entry point function executed by ai.py
# Must override exec_get_func(client, param) where
# client is discord client and params are extra
# parameters from discord or console. If no values
# are inputted for parameters, param will not be
# passed by ai.py and the default value set below
# will be the value for param. exec_get_func() must
# return a string which will be outputted to the
# Discord chat as the bot response to the command
# inputted by the user.
def exec_get_func(client = discord.Client(), param = "today"):
    MonkeyPatch.patch_fromisoformat()
    return "NHL Schedule for " + "{:%b %d, %Y}".format(nhlgb.get_check_date(date_to_check = param)) + "\n\n" + get_nhl_schedule(client = client, date_to_check = param)
