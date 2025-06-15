import discord
from datetime import datetime
import nhl_gamebreak_lib as nhlgb
from backports.datetime_fromisoformat import MonkeyPatch

def get_scores(client = discord.Client(), games_url = "https://nhl-score-api.herokuapp.com/api/scores/latest", date = "today", no_live_games_message = False, league = "NHL"):
    if date == "yesterday":
        return ''

    active_games = nhlgb.get_active_games(games_url, league = league.lower())

    today = datetime.today()
    date_to_check = nhlgb.get_check_date(date_to_check = date).replace(hour = 5, minute = 0)

    timestamp = ""
    scores_string = ""

    counter = 0
    for active_game, active_score in active_games.items():
        report_score = False
        active_game_score = active_score["game_score"]
        game_start_time = datetime.fromisoformat(active_game_score["start_time"].replace("Z", ""))

        if today > date_to_check:
            if game_start_time > date_to_check:
                report_score = True
                if no_live_games_message:
                    counter = counter + 1
        elif no_live_games_message:
            report_score = True
            counter = counter + 1

        if report_score:
            teams = list(active_game_score.keys())
            away_team = teams[0]
            home_team = teams[1]
            away_score = str(active_game_score[away_team])
            home_score = str(active_game_score[home_team])

            timestamp = ""

            emojis = nhlgb.get_emoji_list(discord_client = client)

            if "FINAL" in active_score["state"]:
                scores_string = scores_string + nhlgb.get_final_discord_string(away_team, home_team, away_score, home_score, series_score1 = 0, series_score2 = 0, ot = active_game_score["overtime"], so = active_game_score["shootout"], playoffs = active_score["playoffs"], emojis = emojis) + "\n"
            else:
                if "timestamp" in active_score:
                    timestamp = active_score["timestamp"]

                scores_string = scores_string + nhlgb.get_score_discord_string(away_team, home_team, away_score, home_score, time_remaining = timestamp, emojis = emojis) + "\n"

    if no_live_games_message and counter == 0:
        return "No live games are currently being played!"

    return scores_string


def exec_get_func(client = discord.Client(), param = "today"):
    MonkeyPatch.patch_fromisoformat()
    return "NHL Live Scores for " + "{:%b %d, %Y}".format(nhlgb.get_check_date(date_to_check = param)) + "\n\n" + get_scores(client = client, date = param, no_live_games_message = True)
