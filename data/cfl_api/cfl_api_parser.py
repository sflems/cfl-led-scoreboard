"""
Module that is used for getting basic information about a game
such as the scoreboard and the box score.
"""
from datetime import datetime, timedelta
import requests
import debug
from . import scoreboard_config as sb_config
from . import data as Data
from utils import args
from cfl import CFLClient

ARGS = args()
SB_CONFIG = sb_config.ScoreboardConfig("config", ARGS)
TESTING = SB_CONFIG.testing

REQUEST_TIMEOUT = 10
NETWORK_RETRY_SLEEP_TIME = 10.0

# get current datetime
CURRENT_DATE = datetime.today()
ISO_CURRENT_DATE = CURRENT_DATE.isoformat()
CURRENT_YEAR = CURRENT_DATE.year

BASE_URL = "https://echo.pims.cfl.ca/api"
GAME_OVERVIEW_URL = "{base}/seasons/{season_id}/fixtures/{game_id}?include=play_by_play" # TODO
SCHEDULE_URL = "{base}/seasons/{season_id}/fixtures"
SEASON_URL = "{base}/seasons?year={year}"
STANDINGS_URL = "{base}/standings/{year}" # TODO / NOT EXISTS
PLAYER_URL = "{base}/stats/players/{player_id}"
TEAMS_URL = "{base}/teams"


# Ref: SCHEDULE_URL = "{base}/games?filter[date_start][ge]={day}" + API_KEY
def get_all_games(day=ISO_CURRENT_DATE, year=CURRENT_YEAR):
    try:
        data = {"data": [
            {
                "game_id": 2172,
                "date_start": "2015-06-08T19:30:00-04:00",
                "game_number": 1,
                "week": 1,
                "season": 2015,
                "attendance": 0,
                "event_type": {
                    "event_type_id": 0,
                    "name": "Preseason",
                    "title": ""
                },
                "event_status": {
                    "event_status_id": 4,
                    "name": "Final",
                    "is_active": False,
                    "quarter": 4,
                    "minutes": 0,
                    "seconds": 0,
                    "down": 3,
                    "yards_to_go": 13
                },
                "venue": {
                    "venue_id": 4,
                    "name": "Tim Hortons Field"
                },
                "weather": {
                    "temperature": 21,
                    "sky": "Overcast",
                    "wind_speed": "",
                    "wind_direction": "6km\/h SW",
                    "field_conditions": "Dry"
                },
                "coin_toss": {
                    "coin_toss_winner": "",
                    "coin_toss_winner_election": "Ottawa won coin toss and elected to receive."
                },
                "tickets_url": "http:\/\/www.ticats.ca\/tickets\/",
                "team_1": {
                    "team_id": 6,
                    "location": "Ottawa",
                    "nickname": "Redblacks",
                    "abbreviation": "OTT",
                    "score": 10,
                    "venue_id": 6,
                    "linescores": [
                        {
                            "quarter": 1,
                            "score": 0
                        },
                        {
                            "quarter": 2,
                            "score": 0
                        },
                        {
                            "quarter": 3,
                            "score": 0
                        },
                        {
                            "quarter": 4,
                            "score": 10
                        }
                    ],
                    "is_at_home": False,
                    "is_winner": False
                },
                "team_2": {
                    "team_id": 4,
                    "location": "Hamilton",
                    "nickname": "Tiger-Cats",
                    "abbreviation": "HAM",
                    "score": 37,
                    "venue_id": 4,
                    "linescores": [
                        {
                            "quarter": 1,
                            "score": 7
                        },
                        {
                            "quarter": 2,
                            "score": 13
                        },
                        {
                            "quarter": 3,
                            "score": 14
                        },
                        {
                            "quarter": 4,
                            "score": 3
                        }
                    ],
                    "is_at_home": True,
                    "is_winner": True
                }
            },
            {
                "game_id": 2173,
                "date_start": "2015-06-09T19:30:00-04:00",
                "game_number": 2,
                "week": 2,
                "season": 2015,
                "attendance": 5000,
                "event_type": {
                    "event_type_id": 0,
                    "name": "Preseason",
                    "title": ""
                },
                "event_status": {
                    "event_status_id": 4,
                    "name": "Final",
                    "is_active": False,
                    "quarter": 4,
                    "minutes": 0,
                    "seconds": 0,
                    "down": 1,
                    "yards_to_go": 10
                },
                "venue": {
                    "venue_id": 10,
                    "name": "Toronto: Varsity Stadium"
                },
                "weather": {
                    "temperature": 16,
                    "sky": "Cloudy",
                    "wind_speed": "",
                    "wind_direction": "5 km per  hour",
                    "field_conditions": "Dry, artificial turf"
                },
                "coin_toss": {
                    "coin_toss_winner": "",
                    "coin_toss_winner_election": "Coin toss: Toronto won the toss and elected to receive."
                },
                "tickets_url": "http:\/\/www.argonauts.ca\/tickets\/",
                "team_1": {
                    "team_id": 9,
                    "location": "Winnipeg",
                    "nickname": "Blue Bombers",
                    "abbreviation": "WPG",
                    "score": 34,
                    "venue_id": 9,
                    "linescores": [
                        {
                            "quarter": 1,
                            "score": 3
                        },
                        {
                            "quarter": 2,
                            "score": 10
                        },
                        {
                            "quarter": 3,
                            "score": 14
                        },
                        {
                            "quarter": 4,
                            "score": 7
                        }
                    ],
                    "is_at_home": False,
                    "is_winner": True
                },
                "team_2": {
                    "team_id": 8,
                    "location": "Toronto",
                    "nickname": "Argonauts",
                    "abbreviation": "TOR",
                    "score": 27,
                    "venue_id": 8,
                    "linescores": [
                        {
                            "quarter": 1,
                            "score": 6
                        },
                        {
                            "quarter": 2,
                            "score": 0
                        },
                        {
                            "quarter": 3,
                            "score": 8
                        },
                        {
                            "quarter": 4,
                            "score": 13
                        }
                    ],
                    "is_at_home": True,
                    "is_winner": False
                }
            },
            # ... games continue ...
        ],
            "errors": [

        ],
            "meta": {
            "copyright": "Copyright 2017 Canadian Football League."
        }
        }

        sched = data

        if not TESTING:
            season, week, preseason = get_current_season()
            if preseason:
                week = int(week) - 4 # Preseason uses negative week filter in url
            req_url = SCHEDULE_URL.format(base=BASE_URL, year=season, week_filter=f'&filter[week][eq]={week}')
            #req_url = SCHEDULE_URL.format(base=BASE_URL, year=2023, week_filter=f'&filter[week][eq]=1')
            debug.info(f'Fetching games from: {req_url}')
            data = requests.get(req_url, timeout=REQUEST_TIMEOUT)
            sched = data.json()

        if len(sched['errors']) > 0:
            errors = []
            for error in sched['errors']:
                errors.append(
                    "{} ERROR - ID:{} - {}".format(error['code'], error['id'], error['detail']))
            raise ValueError(errors)

        games = []
        for game in sched['data']:
            output = {
                'id': game['game_id'],  # ID of the game
                'date': game['date_start'],  # Date and time of the game
                # Preseason, Regular Season, Playoffs, Grey Cup, Exhibition
                'game_type': game['event_type']['name'],
                'week': game['week'],
                'season': game['season'],
                'attendance': game['attendance'],

                'state': game['event_status']['name'],   # State of the game.
                'is_active': game['event_status']['is_active'],
                'quarter': game['event_status']['quarter'],
                'time': f"{game['event_status']['minutes']}:{game['event_status']['seconds']}",

                'down': game['event_status']['down'],   # Current down.
                # Current yards to go.
                'spot': game['event_status']['yards_to_go'],

                # Home team name abbreviation
                'home_team_abbrev': game['team_2']['abbreviation'],
                # Home team name
                'home_team_name': game['team_2']['nickname'],
                # ID of the Home team
                'home_team_id': game['team_2']['team_id'],
                'home_score': game['team_2']['score'],  # Home team goals
                'home_win': game['team_2']['is_winner'],  # Home wins

                # Away team name abbreviation
                'away_team_abbrev': game['team_1']['abbreviation'],
                # ID of the Away team
                'away_team_id': game['team_1']['team_id'],
                # Away team name
                'away_team_name': game['team_1']['nickname'],
                'away_score': game['team_1']['score'],  # Away team goals
                'away_win': game['team_1']['is_winner'],  # Away wins
            }
            # put this dictionary into the larger dictionary
            games.append(output)
        return games
    except requests.exceptions.RequestException as e:
        debug.error(e)
        raise ValueError(e)


def get_current_season(year=CURRENT_YEAR):
    try:
        req_url = SEASON_URL.format(
            base=BASE_URL, year=year)
        debug.info(f'Fetching season info from: {req_url}')
        data = requests.get(req_url, timeout=REQUEST_TIMEOUT)
        season_data = data.json()

        if len(season_data['errors']) > 0:
            errors = []
            for error in season_data['errors']:
                errors.append(
                    "{} ERROR - ID:{} - {}".format(error['code'], error['id'], error['detail']))
            raise ValueError(errors)

        season = season_data['data']['current']['season']
        week = season_data['data']['current']['week']
        is_preseason = None

        if week.isnumeric():
            is_preseason = False
        elif week.split("P")[1].isnumeric():
            week = week.split("P")[1]
            is_preseason = True

        return [season, week, is_preseason]

    except requests.exceptions.RequestException as e:
        raise ValueError(e)

# Ref: TEAMS_URL = "{base}/teams"
def get_teams():
    try:
        teams_url = TEAMS_URL.format(base=BASE_URL)
        debug.info(f'Fetching teams from: {teams_url}')
        data = requests.get(teams_url, timeout=REQUEST_TIMEOUT)
        teams = data.json()
        if len(teams['errors']) > 0:
            errors = []
            for error in teams['errors']:
                errors.append(
                    "{} ERROR - ID:{} - {}".format(error['code'], error['id'], error['detail']))
            raise ValueError(errors)
        return teams['data']
    except requests.exceptions.RequestException as e:
        raise ValueError(e)


def get_player(cfl_central_id):
    try:
        data = requests.get(PLAYER_URL.format(
            base=BASE_URL, player_id=cfl_central_id), timeout=REQUEST_TIMEOUT)
        player = data.json()
        if len(player['errors']) > 0:
            errors = []
            for error in player['errors']:
                errors.append(
                    "{} ERROR - ID:{} - {}".format(error['code'], error['id'], error['detail']))
            raise ValueError(errors)
        return player['data'][0]
    except requests.exceptions.RequestException as e:
        raise ValueError(e)


def get_overview(game_id):
    """GAME_OVERVIEW_URL = "{base}/games?filter[game_id][eq]={game_id}&include=boxscore,play_by_play" + API_KEY."""
    try:
        req_url = GAME_OVERVIEW_URL.format(
            base=BASE_URL, game_id=game_id, year=CURRENT_YEAR)
        debug.info(f'Fetching game overview for game_id={game_id} from: {req_url}')
        data = requests.get(req_url, timeout=REQUEST_TIMEOUT)
        game = data.json()

        if len(game['errors']) > 0:
            errors = []
            for error in game['errors']:
                errors.append("{} ERROR - ID:{} - {}".format(error['code'], error['id'], error['detail']))
            raise ValueError(errors)

        play_by_play = game['data'][0]['play_by_play']

        output = {
            'id': game['data'][0]['game_id'],  # ID of the game
            # Date and time of the game
            'date': game['data'][0]['date_start'],
            # Preseason, Regular Season, Playoffs, Grey Cup, Exhibition
            'game_type': game['data'][0]['event_type']['name'],
            'week': game['data'][0]['week'],
            'season': game['data'][0]['season'],
            'attendance': game['data'][0]['attendance'],

            # State of the game.
            'state': game['data'][0]['event_status']['name'],
            'is_active': game['data'][0]['event_status']['is_active'],
            'quarter': game['data'][0]['event_status']['quarter'],
            'minutes': f"{game['data'][0]['event_status']['minutes']:02}",
            'seconds': f"{game['data'][0]['event_status']['seconds']:02}",

            'play_by_play': play_by_play,
            'possession': play_by_play[-1]['team_abbreviation'] if play_by_play else "",
            # Current spot.
            'spot': play_by_play[-1]['field_position_end'] if play_by_play else "",
            'redzone': play_by_play[-1]['is_in_red_zone'] if play_by_play else "",
            # Current down.
            'down': play_by_play[-1]['down'] if play_by_play else "",
            # Current yards to go.
            'ytg': play_by_play[-1]['yards_to_go'] if play_by_play else "",
            # Last play ID
            'play_result_type_id': play_by_play[-1]['play_result_type_id'] if play_by_play else "",

            # Home team name abbreviation
            'home_team_abbrev': game['data'][0]['team_2']['abbreviation'],
            # Home team name
            'home_team_name': game['data'][0]['team_2']['nickname'],
            # ID of the Home team
            'home_team_id': game['data'][0]['team_2']['team_id'],
            # Home team goals
            'home_score': game['data'][0]['team_2']['score'],
            'home_win': game['data'][0]['team_2']['is_winner'],  # Home wins

            # Away team name abbreviation
            'away_team_abbrev': game['data'][0]['team_1']['abbreviation'],
            # ID of the Away team
            'away_team_id': game['data'][0]['team_1']['team_id'],
            # Away team name
            'away_team_name': game['data'][0]['team_1']['nickname'],
            # Away team goals
            'away_score': game['data'][0]['team_1']['score'],
            'away_win': game['data'][0]['team_1']['is_winner'],  # Away wins
        }
    # put this dictionary into the larger dictionary
        return output

    except requests.exceptions.RequestException as e:
        raise ValueError(e)
