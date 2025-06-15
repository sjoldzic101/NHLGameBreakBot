#!/usr/bin/env python3.6
import json
import urllib.request
import sys
import discord
import asyncio
import time
import traceback
import nhl_gamebreak_lib as nhlgb
import subprocess
import os

os.environ['TZ'] = 'America/New_York'
client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

async def start_main_loop():
    await client.wait_until_ready()

    send_to_discord = True
    try:
        old_active_games = {}
        games_url = "https://nhl-score-api.herokuapp.com/api/scores/latest"
        second_to_discord = True
        reload = False
        for arg in sys.argv:
            if arg == "--url=testing":
                games_url = "http://www.vgm2020.com/static/nhl/nhl-test.json"
            elif "--url=" in arg:
                games_url = arg.split('=')[1]
            elif arg == "--reload":
                reload = True
            elif arg == "--onlyconsole":
                send_to_discord = False

        print("Datasource URL: " + games_url)

        emojis = nhlgb.get_emoji_list(discord_client = client)

        if not reload:
            print("Reload mode: Disabled")
            await nhlgb.send_discord_message("Live from Prague, it's NHL GameBreak, the live hockey scores bot! I'm your host, Mettaton. " + nhlgb.get_emoji("FYEAH", emojis = emojis, league = "fyeah"), discord_client = client, send_to_discord = send_to_discord, league = "nhl")
            await nhlgb.send_discord_message("And, as always, I'll be covering the hockey scores for the season. I'm reporting live from Prague, Czechia for " + nhlgb.get_emoji("NSH", emojis = emojis, league = "nhl") + " vs. " + nhlgb.get_emoji("SJS", emojis = emojis, league = "nhl") + " goal updates! LET'S DO THAT HOCKEY!!!!", discord_client = client, send_to_discord = send_to_discord, league = "nhl")
        else:
            print("Reload mode: Enabled")
            print("Reload mode enabled. Killing all previous bot instances...")

            current_pid = os.getpid()
            pids = subprocess.Popen(['/bin/bash', 'get_bot_pids.sh'], stdout=subprocess.PIPE).communicate()[0].decode('UTF-8').rstrip().split('\n')

            for pid in pids:
                if not int(pid) == int(current_pid):
                    subprocess.Popen(['kill', '-9', str(pid)])

        if send_to_discord:
            print("Send to Discord mode: Enabled")
        else:
            print("Send to Discord mode: Disabled")
	
        active_games = nhlgb.get_active_games(games_url)
        while not client.is_closed():
            try:
                active_games = nhlgb.get_active_games(games_url)
                if not old_active_games == {}:
                    for game, score in active_games.items():
                        game_found = False

                        if not game in old_active_games and score["state"] == "LIVE" and not reload:
                            game_score = score["game_score"]
                            teams = list(game_score.keys())
                            away_team = teams[0]
                            home_team = teams[1]

                            score_league = "FYEAH"
                            if "league" in score:
                                score_league = score["league"]

                            await nhlgb.send_discord_message(score_league + ": Puck dropped! " + nhlgb.get_emoji(away_team, emojis = emojis, league = score_league.lower()) + " " + away_team + " at " + nhlgb.get_emoji(home_team, emojis = emojis, league = score_league.lower()) + " " + home_team, discord_client = client, send_to_discord = send_to_discord, league = score_league.lower())
                            break

                        if reload:
                            reload = False
                            
                        for old_game, old_score in old_active_games.items():
                            if game == old_game:
                                game_score = score["game_score"]
                                old_game_score = old_score["game_score"]
                                teams = list(game_score.keys())
                                away_team = teams[0]
                                away_score = game_score[away_team]
                                
                                away_series_score = 0
                                if score["playoffs"]:
                                    away_series_score = score["playoffSeries"][away_team]

                                old_away_score = old_game_score[away_team]
                                home_team = teams[1]
                                home_score = game_score[home_team]
                                old_home_score = old_game_score[home_team]

                                home_series_score = 0
                                if score["playoffs"]:
                                    home_series_score = score["playoffSeries"][home_team]
                                
                                try:
                                    goalscorer = score["latest_goal"]["goal_scorer"]
                                except Exception as e:
                                    goalscorer = " Unknown"

                                try:
                                    assist_by = score["latest_goal"]["assisted_by"]
                                except Exception as e:
                                    assist_by = ", unassisted"

                                try:
                                    timestamp = score["timestamp"]
                                except Exception as e:
                                    timestamp = ""

                                try:
                                    goal_type = score["latest_goal"]["goal_type"]
                                except Exception as e:
                                    goal_type = {}
                                    goal_type["powerplay"] = False
                                    goal_type["shorthanded"] = False
                                    goal_type["empty_net"] = False

                                league = ""
                                if "league" in score:
                                    league = score["league"]


                                if score["state"] == "LIVE":
                                    print(league + " - OLD: " + away_team + " " + str(old_away_score) + " @ " + home_team + " " + str(old_home_score))
                                    print(league + " - CURRENT: " + away_team + " " + str(away_score) + " @ " + home_team + " " + str(home_score))

                                final_string = " FINAL"
                                if not score["game_score"] == old_score["game_score"] and old_score["state"] == "LIVE":
                                    print("score change")
                                    discord_string = ""

                                    if game_score["overtime"]:
                                        timestamp = "OT"
                                        final_string = " FINAL/OT"

                                    if game_score["shootout"]:
                                        timestamp = "SO"
                                        final_string = " FINAL/SO"

                                    league = ""
                                    if "league" in score:
                                        league = score["league"]

                                    if away_score < old_away_score:
                                        discord_string = nhlgb.get_goal_discord_string(away_team, home_team, away_score, home_score, team1_scored = True, time_remaining = timestamp, reversed_goal = True, emojis = emojis, goal_type = goal_type, league = league)
                                    elif home_score < old_home_score:
                                        discord_string = nhlgb.get_goal_discord_string(away_team, home_team, away_score, home_score, team1_scored = False, time_remaining = timestamp, reversed_goal = True, emojis = emojis, goal_type = goal_type, league = league)
                                    elif away_score > old_away_score:
                                        discord_string = nhlgb.get_goal_discord_string(away_team, home_team, away_score, home_score, team1_scored = True, time_remaining = timestamp, goal_scorer = goalscorer, goal_assisted_by = assist_by, emojis = emojis, goal_type = goal_type, league = league)
                                    elif home_score > old_home_score:
                                        discord_string = nhlgb.get_goal_discord_string(away_team, home_team, away_score, home_score, team1_scored = False, time_remaining = timestamp, goal_scorer = goalscorer, goal_assisted_by = assist_by, emojis = emojis, goal_type = goal_type, league = league)

                                    if not discord_string == "":
                                        await nhlgb.send_discord_message(discord_string, discord_client = client, send_to_discord = send_to_discord, league = league)

                                    if "FINAL" in score["state"]:
                                        await nhlgb.send_discord_message(nhlgb.get_final_discord_string(away_team, home_team, away_score, home_score, series_score1 = away_series_score, series_score2 = home_series_score, ot = game_score["overtime"], so = game_score["shootout"], playoffs = score["playoffs"], emojis = emojis), discord_client = client, send_to_discord = send_to_discord, league = league)

                                    if "timestamp" in score and "END" in score["timestamp"]:
                                        await nhlgb.send_discord_message(nhlgb.get_score_discord_string(away_team, home_team, away_score, home_score, time_remaining = timestamp, emojis = emojis, league = league), discord_client = client, send_to_discord = send_to_discord, league = league)
                                    #elif "timestamp" in old_score and "END" in old_score["timestamp"]:
                                    #    await nhlgb.send_discord_message(nhlgb.get_score_discord_string(away_team, home_team, away_score, home_score, time_remaining = "START OF " + timestamp.split(" ")[1], emojis = emojis, league = league), discord_client = client, send_to_discord = send_to_discord, league = league)
                                    break
                                
                                if "FINAL" in score["state"] and not score["state"] == old_score["state"]:
                                    await nhlgb.send_discord_message(nhlgb.get_final_discord_string(away_team, home_team, away_score, home_score, series_score1 = away_series_score, series_score2 = home_series_score, ot = game_score["overtime"], so = game_score["shootout"], playoffs = score["playoffs"], emojis = emojis, league = league), discord_client = client, send_to_discord = send_to_discord, league = league)
                                    break
                                    
                                if "end_period" in score and "end_period" in old_score and "timestamp" in score and "timestamp" in old_score and "END" in score["timestamp"] and not score["timestamp"] == old_score["timestamp"]:
                                    await nhlgb.send_discord_message(nhlgb.get_score_discord_string(away_team, home_team, away_score, home_score, time_remaining = timestamp, emojis = emojis), discord_client = client, send_to_discord = send_to_discord ,league = league)
                                    break
                                
                old_active_games = active_games
                await asyncio.sleep(0.1)
                time.sleep(30)
            except Exception as e:
                print(str(e), file=sys.stderr)
                traceback.print_exc()
        
        #print("TOR " + str(active_games["TORatCBJ"]["TOR"]) + " CBJ " + str(active_games["TORatCBJ"]["CBJ"]))
    except Exception as e:
        print(str(e), file=sys.stderr)
        pass

def main():
    print("NHL GameBreak Bot Notifications Server v1.0. Initializing....")
    client.loop.create_task(start_main_loop())
    client.run(nhlgb.get_settings()['token'])

main()
