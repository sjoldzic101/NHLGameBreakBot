import urllib, discord, json

def get_nhl_games(url = "https://nhl-score-api.herokuapp.com/api/scores/latest"):
    data = urllib.request.urlopen(url).read().decode()
    return json.loads(data)["games"]

def get_nhl_active_games(url = "https://nhl-score-api.herokuapp.com/api/scores/latest"):
    games = get_nhl_games(url)
    scorelines = {}
    for game in games:
        if game["status"]["state"] == "LIVE" or game["status"]["state"] == "FINAL":
            gamedata = {}
            scoreline = {}
            for team_abbr in game["scores"]:
                scoreline[team_abbr] = game["scores"][team_abbr]
            scoreline["overtime"] = False
            scoreline["shootout"] = False
            scoreline["start_time"] = game["startTime"]

            if "overtime" in game["scores"]:
                scoreline["overtime"] = game["scores"]["overtime"]
            
            if "shootout" in game["scores"]:
                scoreline["shootout"] = game["scores"]["shootout"]

            gamedata["game_score"] = scoreline
            gamedata["state"] = game["status"]["state"]

            gamedata["playoffs"] = False
            if "playoffSeries" in game:
                gamedata["playoffs"] = True
                gamedata["playoffSeries"] = game["playoffSeries"]

            gamedata["latest_goal"] = ""
            if 'goals' in game and len(game["goals"]) > 0:
                latest_goal = game["goals"][-1]
                latest_goal_scored = {}

                goal_scorer_season_total = 0
                goal_scorer = "Unknown"

                if "scorer" in latest_goal:
                    if "seasonTotal" in latest_goal["scorer"]:
                        goal_scorer_season_total = latest_goal["scorer"]["seasonTotal"]

                    if "player" in latest_goal["scorer"]:
                        goal_scorer = latest_goal["scorer"]["player"]

                if goal_scorer is None:
                    goal_scorer = "Unknown"

                latest_goal_scored["goal_scorer"] = goal_scorer + " (" + str(goal_scorer_season_total) + ")"
                goals_assisted_by = ""
                
                if "assists" in latest_goal:
                    for assister in latest_goal["assists"]:
                        assists_season_total = 0

                        if "seasonTotal" in assister:
                            assists_season_total = assister["seasonTotal"]

                        goals_assisted_by = goals_assisted_by + assister["player"] + " (" + str(assists_season_total) +"), "
                    goals_assisted_by = goals_assisted_by[:-2]

                latest_goal_scored["assisted_by"] = goals_assisted_by


                goal_type = {}
                goal_type["powerplay"] = False
                goal_type["shorthanded"] = False
                goal_type["empty_net"] = False

                if "strength" in latest_goal:
                    if latest_goal["strength"] == "PPG":
                        goal_type["powerplay"] = True
                    elif latest_goal["strength"] == "SHG":
                        goal_type["shorthanded"] = True

                if "emptyNet" in latest_goal and latest_goal["emptyNet"] == True:
                    goal_type["empty_net"] = True

                latest_goal_scored["goal_type"] = goal_type

                gamedata["latest_goal"] = latest_goal_scored

            if game["status"]["state"] == "LIVE":    
                current_period = game["status"]["progress"]["currentPeriodOrdinal"]
                time_remaining = game["status"]["progress"]["currentPeriodTimeRemaining"]["pretty"]
                gamedata["timestamp"] = time_remaining + " " + current_period
                gamedata["end_period"] = False
                if "min" in game["status"]["progress"]["currentPeriodTimeRemaining"] and "sec" in game["status"]["progress"]["currentPeriodTimeRemaining"] and min == 0 and min == sec:
                    gamedata["end_period"] = True
            else:
                time_remaining = "FINAL"
  
            away_abbr = game["teams"]["away"]["abbreviation"]
            home_abbr = game["teams"]["home"]["abbreviation"]
            gamedata["league"] = "NHL"
            scorelines[away_abbr + "at" + home_abbr] = gamedata
    return scorelines

def exec_get_func(url = "https://nhl-score-api.herokuapp.com/api/scores/latest"):
    return get_nhl_active_games(url)
