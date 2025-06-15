import discord
import json
import urllib.request
import nhl_gamebreak_lib as nhlgb

# taken from https://www.saltycrane.com/blog/2007/12/how-to-sort-table-by-columns-in-python/ and https://python-forum.io/Thread-How-do-you-sort-a-table-by-one-column-of-floats
def sort_table(table, col=0):
    return sorted(table, key=lambda k: int(k[col]))

def get_nhl_standings(url = "https://statsapi.web.nhl.com/api/v1/standings/regularSeason", division = "all"):
    division = division.capitalize()

    data = urllib.request.urlopen(url).read().decode()

    standings = json.loads(data)["records"]

    division_ids = {}

    division_ids["Central_id"] = 0
    division_ids["East_id"] = 0
    division_ids["West_id"] = 0
    division_ids["North_id"] = 0

    counter = 0
    for division_entry in standings:
        division_name = division_entry["division"]["name"]
        if "Central" in division_name:
            division_ids["Central_id"] = counter
        elif "East" in division_name:
            division_ids["East_id"] = counter
        elif "West" in division_name:
            division_ids["West_id"] = counter
        elif "North" in division_name:
            division_ids["North_id"] = counter
        else:
            counter = counter + 1
            pass

        counter = counter + 1

    division_id_min = 0
    division_id_max = 0
    if division == "Central":
        division_id_min = division_ids["Central_id"]
        division_id_max = division_ids["Central_id"]
    elif division == "East":
        division_id_min = division_ids["East_id"]
        division_id_max = division_ids["East_id"]
    elif division == "West":
        division_id_min = division_ids["West_id"]
        division_id_max = division_ids["West_id"]
    elif division == "North":
        division_id_min = division_ids["North_id"]
        division_id_max = division_ids["North_id"]
    else:
        division_id_max = 3

    standings_output = standings[division_id_min]["teamRecords"]

    if division_id_max > division_id_min:
        for i in range(division_id_min + 1, division_id_max + 1):
            standings_output = standings_output + standings[i]["teamRecords"]

    return standings_output

def get_standings_string(client = discord.Client(), division = "all"):
    division = division.capitalize()

    emojis = nhlgb.get_emoji_list(discord_client = client)

    if not division == "Central" and not division == "East" and not division == "West" and not division == "North" and not division == "All":
        return "Error! Division name not recognized!"

    header = division + " Division"
    if header == "All Division":
        header = "Entire League"
    header = "NHL Standings - " + header + "\n\n"

    standings_string = ""

    standings_dict = get_nhl_standings(division = division)

    index = "divisionRank"
    if division == "All":
        index = "leagueRank"

    team_emoji = ""
    modified_standings_list = []
    for team in standings_dict:
        team_abbr = nhlgb.get_abbr(team["team"]["name"])
        team_emoji = nhlgb.get_emoji(team_abbr, emojis= emojis)
        team_info = [team[index], team["gamesPlayed"], team["leagueRecord"]["wins"], team["leagueRecord"]["losses"], team["leagueRecord"]["ot"], team["points"], team_emoji + " " + team_abbr]
        modified_standings_list.append(team_info)


    header_table = [["Rank", "GP", "W", "L", "OT", "Points", "Team"]]
    for header_row in header_table:
        standings_string = standings_string + "{: <5} {: >5} {: >10} {: >10} {: >10} {: >10} {: >10}".format(*header_row) + "\n"

    sorted_table = sort_table(modified_standings_list, 0)
    for team_row in sorted_table:
        standings_string = standings_string + "{: <10} {: >5} {: >15} {: >10} {: >8} {: >10} {: >50}".format(*team_row) + "\n"

    standings_string = header + standings_string

    return standings_string

def exec_get_func(client = discord.Client(), param = "all"):
    return get_standings_string(client = client, division = param)
