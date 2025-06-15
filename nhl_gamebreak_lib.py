#!/usr/bin/env python3.6
import json
import urllib.request
import sys
import discord
import asyncio
import time
import traceback
import importlib
from datetime import datetime, timedelta
from backports.datetime_fromisoformat import MonkeyPatch

if sys.version_info > (3, 7):
    from pynput.keyboard import Key, Controller

# taken from https://stackoverflow.com/questions/11122291/how-to-find-char-in-string-and-get-all-the-indexes
def find(s, ch):
    return [i for i, ltr in enumerate(s) if ltr == ch]

def get_check_date(date_to_check = "today"):
    check_date = datetime.today()

    if not date_to_check == "today":
        if date_to_check == "tomorrow":
            check_date += timedelta(days=1)
        elif date_to_check == "yesterday":
            check_date -= timedelta(days=1)
        else:
            check_date = datetime.strptime(date_to_check, '%m-%d-%Y')

    return check_date

def get_config(config_filepath = "nhl-settings.json"):
    with open(config_filepath,"r") as nhl_teams_file:
        return(json.load(nhl_teams_file))

def get_settings():
    return get_config()["settings"]

def get_guild_list():
    return get_settings()["guilds"]

def get_name(team_name, league = "nhl"):
    teams = get_config()["leagues"][league]["teams"]
    return teams[team_name]["name"]

def get_abbr(team_full_name, league = "nhl"):
    teams = get_config()["leagues"][league]["teams"]
    abbr = ""

    for team_abbr, team_data in teams.items():
        if team_full_name in team_data["name"]:
            abbr = team_abbr
            break

    return abbr

def get_emoji(team_name, emojis = None, league = "nhl"):
    teams = get_config()["leagues"][league]["teams"]
    emoji_value = ""

    if team_name in teams:
        emoji_value = teams[team_name]["emoji"]

    if not emojis is None:
        for emoji in emojis:
            if emoji_value in emoji:
                emoji_value = str(emoji)
                break

    return emoji_value
        
def get_active_games(url = "", league = "all"):
    import nhl_lib #,nwhl_lib
    games = {}
    if league == "nhl":
        games = nhl_lib.exec_get_func(url = url)
    #elif league == "phf":
    #    games = nwhl_lib.exec_get_func()
    elif league == "all":
        games = nhl_lib.exec_get_func(url = url)
    #    games.update(nwhl_lib.exec_get_func(url = url))

    return games

def get_goal_discord_string(team1, team2, score1, score2, team1_scored = False, time_remaining = "", goal_scorer = "", goal_assisted_by = "", reversed_goal = False, emojis = None, goal_type = None, league = "NHL"):
    team1_name = get_name(team1, league = league.lower())
    team1_emoji = get_emoji(team1, emojis, league = league.lower()) 
    team2_name = get_name(team2, league = league.lower())
    team2_emoji = get_emoji(team2, emojis, league = league.lower())

    if not time_remaining == "" and not time_remaining is None:
        time_remaining = " " + time_remaining
    else:
        time_remaining = "N/A"

    if not goal_scorer == "" and not goal_scorer is None:
        goal_scorer = ". Goal scored by " + goal_scorer
    else:
        goal_scorer = " Unknown"

    if not goal_assisted_by is None:
        if goal_assisted_by == "":
            goal_assisted_by = ", unassisted"
        else:
            goal_assisted_by = ", assisted by " + goal_assisted_by
    else:
            goal_assisted_by = ", assisted by Unknown"


    goal_string = ""
    if not goal_type is None:
        if "powerplay" in goal_type and goal_type["powerplay"]:
            goal_string = goal_string + " PP" 
        elif "shorthanded" in goal_type and goal_type["shorthanded"]:
            goal_string = goal_string + " SH"

        if "empty_net" in goal_type and goal_type["empty_net"]:
            goal_string = goal_string + " EN"

    if team1_scored:
        goal_string = team1 + goal_string
    else:
        goal_string = team2 + goal_string

    goal_string = league + ": " + goal_string + " GOAL! "

    if reversed_goal:
        goal_string = league + ": Reversed goal! "
        goal_scorer = ""
        goal_assisted_by = ""

    return(goal_string + team1_emoji + " " + team1 + " " + str(score1) + " " + team2_emoji + " "
          + team2 + " " + str(score2) + time_remaining + goal_scorer + goal_assisted_by)

def get_score_discord_string(team1, team2, score1, score2, time_remaining = "", emojis = None, league = "NHL"):
    team1_name = get_name(team1, league = league.lower())
    team1_emoji = get_emoji(team1, emojis, league = league.lower()) 
    team2_name = get_name(team2, league = league.lower())
    team2_emoji = get_emoji(team2, emojis, league = league.lower())

    if not time_remaining == "" and not time_remaining is None:
        time_remaining = " " + time_remaining
    else:
        time_remaining = "N/A"

    return(league + ": " + team1_emoji + " " + team1 + " " + str(score1) + " " + team2_emoji + " " + team2 + " " + str(score2) + time_remaining)


def get_emoji_list(guild_ids = [520433296732323860, 805575041479606292], discord_client = discord.Client()):
    emoji_list = []

    for guild_id in guild_ids:
        emojis = discord_client.get_guild(guild_id).emojis
        for emoji in emojis:
            emoji_list.append(str(emoji))

    return emoji_list

def get_final_discord_string(team1, team2, score1, score2, series_score1 = 0, series_score2 = 0, ot = False, so = False, playoffs = False, emojis = None, league = "NHL"):
    team1_name = get_name(team1, league = league.lower())
    team1_emoji = get_emoji(team1, emojis, league = league.lower()) 
    team2_name = get_name(team2, league = league.lower())
    team2_emoji = get_emoji(team2, emojis, league = league.lower())

    score_string = team1_emoji + " " + team1 + " " + str(score1) + " " + team2_emoji + " " + team2 + " " + str(score2)
    final_string = " FINAL"
    series_score = ""

    if ot:
        final_string = " FINAL/OT"
    elif so:
        final_string = " FINAL/SO"

    if playoffs:
        if series_score1 == series_score2:
            series_score = " (Series tied " + str(series_score1) + "-" + str(series_score2) + ")"
        elif series_score1 > series_score2:
            if series_score1 == 4:
                series_score = " (" + team1 + " wins series " + str(series_score1) + "-" + str(series_score2) + ")"
            else:
                series_score = " (" + team1 + " leads series " + str(series_score1) + "-" + str(series_score2) + ")"
        else:
            if series_score2 == 4:
                series_score = " (" + team1 + " wins series " + str(series_score1) + "-" + str(series_score2) + ")"
            else:
                series_score = " (" + team2 + " leads series " + str(series_score2) + "-" + str(series_score1) + ")"

    score_string = league + ": " + score_string + final_string + series_score

    return score_string

async def send_discord_message(message, channel_id = 0, discord_client = discord.Client(), console_mode = False, send_to_discord=False, from_console = False, league = "none"):
    for guild_id, guild_info in get_guild_list().items():
        if channel_id == int(guild_info["channel"]) or ((guild_info["leagues"] == "all" or guild_info["leagues"] == league.lower()) and not league == "none"):
            max_discord_msg_length = 1999
            message_pt1 = message.encode('ascii', 'ignore').decode('ascii')
            message_pt2 = ""
       
            if len(message) > max_discord_msg_length:
                index = 0
                for i in find(message, '\n'):
                    if i > max_discord_msg_length:
                        break
                    index = i
        
                if not index == 0:
                    message_pt1 = message[:index]
                    message_pt2 = message[index+1:]
            if console_mode:
                if sys.version_info > (3, 7) and from_console:
                    keyboard = Controller()
                    keyboard.press(Key.enter)
                    keyboard.release(Key.enter)
        
            if send_to_discord:
                print("Sending message \"" + message + "\" to channel id \"" + guild_info["channel"] + "\"...")

                channel = discord_client.get_channel(int(guild_info["channel"]))

                if not channel is None:
                    if not message_pt1 is None and not message_pt1 == "":
                        await channel.send(message_pt1)
                    if not message_pt2 is None and not message_pt2 == "":
                        await channel.send(message_pt2)
            else:
                print("Output: " + message)

async def send_dm(user, message, discord_client = discord.Client()):
    user_message = discord_client.get_user(user)
    await user_message.send(message)
