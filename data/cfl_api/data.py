from datetime import datetime, timedelta
import time as t
import logging
from tzlocal import get_localzone
from . import cfl_api_parser

debug = logging.getLogger("cfl-scoreboard")


class Data:
    def __init__(self, config):
        """Initiate settings to control board and CFL API info for renderer."""
        # Save the parsed config
        self.config = config

        # Flag to determine when to refresh data
        self.first_refresh = True
        self.needs_refresh = True

        # What game do we want to start on?
        self.current_game_index = 0
        self.current_division_index = 0

        # Parse today's date and see if we should use today or yesterday
        self.get_current_date()

        # TODO: self.playoffs = cfl_api_parser.is_playoffs()
        self.today = self.get_today()
        self.time_since_day_refresh = t.time()
        self.current_week = None
        self.current_season = None
        self.preseason = None

        # Teams
        #self.teams = cfl_api_parser.get_teams()

        # Fetch the teams info
        self.games_refresh_time = config.data_refresh_rate
        self.games = []
        self.refresh_games()

    def get_today(self):
        """Get current todays day."""
        return datetime.now(get_localzone()).day

    def get_current_date(self):
        """Get current local datetime."""
        return datetime.now(get_localzone())

    # Get All Games
    def refresh_games(self, game_id=None):
        """Refresh games list, if game_id passed, get overview."""
        attempts_remaining = 5
        while attempts_remaining > 0:
            if game_id is None:
                time_since_refresh = t.time() - self.games_refresh_time
                if not time_since_refresh > self.config.data_refresh_rate:
                    delay = self.config.data_refresh_rate - time_since_refresh
                    debug.warning(f"Rate limiting games refresh. Sleeping for {round(delay)}s")
                    time_since_day_start = t.time() - self.time_since_day_refresh

                    if time_since_day_start > 86400:
                        self.current_week = cfl_api_parser.get_current_season()
                        self.current_week = self.current_week[1]

                    t.sleep(self.config.data_refresh_rate -
                            time_since_refresh)

                self.games = cfl_api_parser.get_all_games()

                if self.config.rotation_only_preferred and self.config.preferred_teams:
                    debug.info(f'Filtering games for preferred team - {self.config.preferred_teams}')
                    self.games = self.__filter_list_of_games(
                    self.games, self.config.preferred_teams)

                self.games_refresh_time = t.time()
                self.needs_refresh = False
                self.network_issues = False


            else:
                try:
                    if not hasattr(self, "games_refresh_time"):
                        self.games_refresh_time = 0
                    time_since_refresh = t.time() - self.games_refresh_time
                    if not self.first_refresh and not time_since_refresh > self.config.data_refresh_rate:
                        delay = self.config.data_refresh_rate - time_since_refresh
                        debug.warning(f"Rate limiting get_overview({game_id}). Sleeping for {round(delay)}s")
                        t.sleep(
                            self.config.data_refresh_rate - time_since_refresh)
                    self.games[self.current_game_index] = cfl_api_parser.get_overview(
                        game_id)

                    self.first_refresh = False
                    self.games_refresh_time = t.time()
                    self.needs_refresh = False
                    self.network_issues = False
                    break

                except ValueError as e:
                    self.network_issues = True
                    debug.error(f"ValueError while refreshing single game overview - ID: {game_id}. {attempts_remaining} retries remaining.")
                    debug.error(f"Error(s): {e}")
                    attempts_remaining -= 1
                    t.sleep(cfl_api_parser.NETWORK_RETRY_SLEEP_TIME)

                except Exception as e:
                    self.network_issues = True
                    debug.error(f"Networking error while refreshing single game overview - ID: {game_id}. {attempts_remaining} retries remaining.")
                    debug.error(f"Exception(s): {e}")
                    attempts_remaining -= 1
                    t.sleep(cfl_api_parser.NETWORK_RETRY_SLEEP_TIME)

        # If we run out of retries, just move on to the next game
        if attempts_remaining <= 0 and self.config.rotation_enabled:
            self.advance_to_next_game()

    def get_gametime(self):
        """Return the current game gametime."""
        raw_gt = datetime.strptime(
            self.games[self.current_game_index]['date'], "%Y-%m-%dT%H:%M:%S%z")
        tz = get_localzone()
        # gametime = datetime.strptime(self.games[self.current_game_index]['date'], "%Y-%m-%dT%H:%M:%S%z") + timedelta(hours=(tz_diff / 60 / 60 * -1))
        gametime = raw_gt.astimezone(tz)
        return gametime

    def showing_preferred_game(self):
        """Check if showing preferred team in current game."""
        # next_game = self.games[self.__next_game_index()]
        showing_preferred_team = False
        if self.games:
            current_game = self.games[self.current_game_index]

            if self.config.preferred_teams and self.config.preferred_teams[0] in [current_game['home_team_abbrev'], current_game['away_team_abbrev']] and current_game['state'] == 'In-Progress':
                showing_preferred_team = True
            elif len(self.config.preferred_teams) > 1:
                for team in self.config.preferred_teams:
                    if team in [current_game['home_team_abbrev'], current_game['away_team_abbrev']] and current_game['state'] == 'In-Progress':
                        showing_preferred_team = True

        debug.info(f"showing_preferred_game = {showing_preferred_team} {'(Live)' if showing_preferred_team else '(Not Live)'}")
        return showing_preferred_team

    def advance_to_next_game(self):
        """Advances game index to next game."""
        debug.info("Advancing to next game.")
        self.current_game_index = self.__next_game_index()

    def __filter_list_of_games(self, games, teams):
        """Filters games list for preferred teams."""
        # Return all games if current preferred game live?
        if self.config.rotation_preferred_team_live_enabled and self.showing_preferred_game():
            return games

        # Return all games if current preferred game halftime
        # if self.games:
        halftime = False
            #halftime = self.games[self.current_game_index]['quarter'] == 2 and self.games[
            #    self.current_game_index]['minutes'] == 0 and self.games[self.current_game_index]['seconds'] == 0

        if self.config.rotation_preferred_team_live_halftime and self.showing_preferred_game() and halftime:
            return games

        filtered_games = [game for game in games if set(
            [game['away_team_abbrev'], game['home_team_abbrev']]).intersection(set(teams))]

        # Return all games if no preferred games are found.
        if not filtered_games:
            return games

        return filtered_games

    def __next_game_index(self):
        """Returns next game index."""
        counter = self.current_game_index + 1
        if counter >= len(self.games):
            counter = 0
        return counter
