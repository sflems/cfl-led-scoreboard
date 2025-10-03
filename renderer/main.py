import time as t
from datetime import  timedelta
import logging
from numpy import kaiser
from tzlocal import get_localzone
from PIL import Image, ImageFont, ImageDraw
from utils import center_text, calculate_aspect, get_logo

debug = logging.getLogger("cfl-scoreboard")


class MainRenderer:
    def __init__(self, matrix, data):
        """Initiates board renderer settings and displays CFL games."""
        self.matrix = matrix
        self.data = data
        self.canvas = matrix.CreateFrameCanvas()
        self.width = matrix.width
        self.height = matrix.height
        self.aspect = calculate_aspect(self.width, self.height)

        debug.info(f"Aspect ratio detected: {self.aspect} ({self.width}x{self.height})")

        # Create a new data image.
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        # Load the fonts
        font_multiplier = int(self.height / 32)
        self.font = ImageFont.truetype("fonts/score_large.otf", 16 * font_multiplier)
        self.font_15 = ImageFont.truetype("fonts/score_large.otf", 15 * font_multiplier)
        self.font_small = ImageFont.truetype("fonts/04B_24__.TTF", 12 * font_multiplier)
        self.font_mini = ImageFont.truetype("fonts/04B_24__.TTF", 8 * font_multiplier)

    def render(self):
        """Displays CFL games on board depending on state."""
        while True:
            self.starttime = t.time()
            self.data.get_current_date()
            self.__render_game()

    def __render_game(self):
        while True:
            debug.info("Starting render.")
            # If we need to refresh the overview data, do that
            if self.data.needs_refresh:
                self.data.refresh_games()

            debug.info(f"Games list/data to render: {self.data.games}")

            game = self.data.games[self.data.current_game_index]

            # Set the refresh rate
            rotate_rate = self.__rotate_rate_for_game(game)
            refresh_rate = self.data.config.data_refresh_rate
            debug.info(f'Refresh rate: {refresh_rate}s')

            endtime = t.time()
            time_delta = endtime - self.starttime

            if time_delta >= refresh_rate and self.data.needs_refresh:
                self.starttime = t.time()
                self.data.needs_refresh = True
                debug.info("Needs refresh!")

            if endtime - self.data.games_refresh_time >= refresh_rate:
                self.data.needs_refresh = True
                debug.info("Needs refresh!")

            # Draw the current game
            self.__draw_game(game)
            t.sleep(rotate_rate)

            if self.__should_rotate_to_next_game(game):
                return self.data.advance_to_next_game()

    def __rotate_rate_for_game(self, game):
        if game['state'] == 'Pre-Game':
            rotate_rate = self.data.config.rotation_rates_pregame
            debug.info(f'Setting pre-game rotation rate: {rotate_rate}s')
        elif game['state'] == 'Final':
            rotate_rate = self.data.config.rotation_rates_final
            debug.info(f'Setting post game rotation rate: {rotate_rate}s')
        else:
            rotate_rate = self.data.config.rotation_rates_live
            debug.info(f'Setting rotation rate: {rotate_rate}s')
        return rotate_rate

    def __should_rotate_to_next_game(self, game):
        rotate = self.data.config.rotation_enabled
        live_game = self.data.showing_preferred_game()
        halftime_rotate = live_game and self.data.config.rotation_preferred_team_live_halftime

        if live_game and self.data.config.rotation_preferred_team_live_enabled:
            if halftime_rotate and hasattr(game, 'play_by_play') and game['play_by_play'][-1]['play_result_type_id'] == 8:
                debug.info("Halftime rotate!")
                rotate = True
            else:
                debug.info("Live rotate!")
                rotate = True

        debug.info(f'__should_rotate_to_next_game? {rotate}')
        return rotate

    def __draw_game(self, game):
        debug.info(f'Drawing game. __draw_game({game["id"]})')

        gametime = self.data.get_gametime()
        one_hour_pregame = gametime - timedelta(hours=1)

        if game['state'] == 'In-Progress':
            debug.info(f'State: Live Game, checking every {self.__rotate_rate_for_game(game)}s')
            self.data.refresh_games(game['id'])
            game = self.data.games[self.data.current_game_index]
            self._draw_live_game(game)
        elif game['state'] == 'Final':
            debug.info('State: Post-Game')
            self._draw_post_game(game)
        elif gametime.now(get_localzone()) > one_hour_pregame and game['state'] == 'Pre-Game':
            debug.info('Countdown til gametime')
            self._draw_countdown(game)
        elif game['state'] == 'Pre-Game':
            debug.info('State: Pre-Game')
            self._draw_pregame(game)
        elif game['state'] == 'Postponed' or game['state'] == 'Cancelled':
            debug.info(f'State: Game {game["state"]}.')
            self.data.advance_to_next_game()
            self.__render_game()

        if self.data.needs_refresh:
            self.data.refresh_games()

    def _draw_pregame(self, game):
        time = self.data.get_current_date()
        gamedatetime = self.data.get_gametime()
        if gamedatetime.day == time.day and gamedatetime.month == time.month:
            date_text = 'TODAY'
        else:
            date_text = gamedatetime.strftime('%a %b %-d').upper()
        gametime = gamedatetime.strftime("%-I:%M %p")

        # TEMP Open the logo image file
        away_team_logo = get_logo(game['away_team_abbrev'], self.height, self.data.config.helmet_logos)
        home_team_logo = get_logo(game['home_team_abbrev'], self.height, self.data.config.helmet_logos)

        # Flip home logo if using helmets
        if self.data.config.helmet_logos is True:
            home_team_logo = home_team_logo.transpose(Image.FLIP_LEFT_RIGHT)
            # Put the images on the canvas
            self.image.paste(away_team_logo, (round(-0.17 * self.width ), 0), mask=away_team_logo)
            self.image.paste(home_team_logo, (round(0.61 * self.width ), 0), mask=home_team_logo)

        else:
            # Put the images on the canvas
            if game['home_team_abbrev'] == "CGY":
                self.image.paste(home_team_logo, (round(0.505 * self.width), round(0.12 * self.height)), mask=home_team_logo)
            else:
                self.image.paste(home_team_logo, (round(0.585 * self.width), round(0.12 * self.height)), mask=home_team_logo)
            self.image.paste(away_team_logo, (round(-0.11 * self.width), round(0.12 * self.height)), mask=away_team_logo)

        # Center the game time on screen
        date_pos = center_text(self.font_mini.getlength(date_text), self.width / 2)
        gametime_pos = center_text(self.font_mini.getlength(gametime), self.width / 2)

        # Draw the text on the Data image.
        self.draw.text((date_pos, 0), date_text, font=self.font_mini, stroke_width=1, stroke_fill=(0,0,0))
        self.draw.multiline_text((
            gametime_pos, round(0.1875 * self.height)),
            gametime,
            fill=(255, 255, 255),
            stroke_width=1,
            stroke_fill=(0,0,0),
            font=self.font_mini,
            align="center")
        self.draw.text((round(0.391 * self.width), round(0.46875 * self.height)), 'VS', font=self.font, stroke_width=1, stroke_fill=(0,0,0))
        # Put the data on the canvas
        self.canvas.SetImage(self.image, 0, 0)
        # Load the canvas on screen.
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
        # Refresh the Data image.
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

    def _draw_countdown(self, game):
        time = self.data.get_current_date()
        game_time = self.data.get_gametime()
        if not time < game_time:
            gametime = 'Kickoff!'
        else:
            gt_diff = game_time - time
            min_to_go = round(gt_diff.total_seconds() / 60)
            gametime = f'{min_to_go} min'

        # TEMP Open the logo image file
        away_team_logo = get_logo(game['away_team_abbrev'], self.height, self.data.config.helmet_logos)
        home_team_logo = get_logo(game['home_team_abbrev'], self.height, self.data.config.helmet_logos)

        # Flip home logo if using helmets
        if self.data.config.helmet_logos is True:
            home_team_logo = home_team_logo.transpose(Image.FLIP_LEFT_RIGHT)
            # Put the images on the canvas
            self.image.paste(away_team_logo, (round(-0.17 * self.width ), 0), mask=away_team_logo)
            self.image.paste(home_team_logo, (round(0.61 * self.width ), 0), mask=home_team_logo)

        else:
            # Put the images on the canvas
            if game['home_team_abbrev'] == "CGY":
                self.image.paste(home_team_logo, (round(0.505 * self.width), round(0.12 * self.height)), mask=home_team_logo)
            else:
                self.image.paste(home_team_logo, (round(0.585 * self.width), round(0.12 * self.height)), mask=home_team_logo)
            self.image.paste(away_team_logo, (round(-0.11 * self.width), round(0.12 * self.height)), mask=away_team_logo)

        # Center the game time on screen.
        gametime_pos = center_text(self.font_mini.getlength(gametime), self.width / 2)

        # Draw the text on the Data image.
        self.draw.text((round(0.4531 * self.width), 0), 'IN', font=self.font_mini, stroke_width=1, stroke_fill=(0,0,0))
        self.draw.multiline_text((gametime_pos, round(0.1875 * self.height)), gametime, fill=(255, 255, 255), font=self.font_mini, align="center", stroke_width=1, stroke_fill=(0,0,0))
        self.draw.text((round(0.391 * self.width), round(0.46875 * self.height)), 'VS', font=self.font, stroke_width=1, stroke_fill=(0,0,0))

        # Put the data on the canvas
        self.canvas.SetImage(self.image, 0, 0)

        # Load the canvas on screen.
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

        # Refresh the Data image.
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        # t.sleep(1)

    def _draw_live_game(self, game):
        last_play_code = game['play_result_type_id']

        # Use this code if you want the animations to run
        if last_play_code == 1:
            debug.info('should draw TD')
            self._draw_td()
        elif last_play_code == 2:
            debug.info('should draw FG')
            self._draw_fg()

        # TEMP Open the logo image file
        away_team_logo = get_logo(game['away_team_abbrev'], round(0.625 * self.height), self.data.config.helmet_logos)
        home_team_logo = get_logo(game['home_team_abbrev'], round(0.625 * self.height), self.data.config.helmet_logos)

        # Flip home logo if using helmets
        if self.data.config.helmet_logos is True:
            home_team_logo = home_team_logo.transpose(Image.FLIP_LEFT_RIGHT)

        # Put the images on the canvas
        self.image.paste(away_team_logo, (round(0.0156 * self.width), 0), mask=away_team_logo)
        self.image.paste(home_team_logo, (round(0.672 * self.width), 0), mask=home_team_logo)

        # Prepare the data
        homescore = '{0:02d}'.format(game['home_score'])
        awayscore = '{0:02d}'.format(game['away_score'])
        quarter = f"Q{game['quarter']}"

        minutes = f"{game['minutes']}" if game['minutes'] else None
        seconds = f"{game['seconds']}" if game['seconds'] else None
        time_period = f"{minutes}:{seconds}" if minutes and seconds else ""
        pos_colour = (255, 255, 255)

        if game['redzone']:
            pos_colour = (255, 25, 25)

        # Set the position of the information on screen.
        home_score_size = self.font.length(homescore)
        time_period_pos = center_text(self.font_mini.getlength(time_period), self.width / 2)
        quarter_pos = center_text(self.font_small.getlength(quarter), self.width / 2)

        # Draw Quarter
        self.draw.multiline_text((quarter_pos, 0), quarter, fill=(255, 255, 255), font=self.font_small, align="center", stroke_width=1, stroke_fill=(0,0,0))

        # Draw Time
        self.draw.multiline_text((time_period_pos, round(0.33 * self.height)), time_period, fill=(255, 255, 255), font=self.font_mini, align="center", stroke_width=1, stroke_fill=(0,0,0))
 
        # Draw Possession & Down
        if game['down'] and game['ytg']:
            down = f"{game['down']}&{game['ytg']}"
            if game['possession'] == game['away_team_abbrev']:
                down = f"<> {down}"
            elif game['possession'] == game['home_team_abbrev']:
                down = f" {down} <>"
            info_pos = center_text(self.font_mini.getlength(down), self.width / 2)
            self.draw.multiline_text((info_pos, round(0.5937 * self.height)), down, fill=(pos_colour), font=self.font_mini, align="center", stroke_width=1, stroke_fill=(0,0,0))

        # Draw Ball Spot
        if game['spot']:
            spot = f"{game['spot']}"
            info_pos = center_text(self.font_mini.getlength(spot), self.width / 2)
            self.draw.multiline_text((info_pos, round(0.7812 * self.height)), spot, fill=(pos_colour), font=self.font_mini, align="center", stroke_width=1, stroke_fill=(0,0,0))

        # Draw Scores
        self.draw.multiline_text((round(0.0938 * self.width), round(0.5938 * self.height)), awayscore, fill=(255, 255, 255), font=self.font, align="center", stroke_width=1, stroke_fill=(0,0,0))
        self.draw.multiline_text((round(0.9219 * self.width) - home_score_size, round(0.5938 * self.height)), homescore, fill=(255, 255, 255), font=self.font, align="center", stroke_width=1, stroke_fill=(0,0,0))

        # Put the data on the canvas
        self.canvas.SetImage(self.image, 0, 0)

        # Load the canvas on screen.
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

        # Refresh the Data image.
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        # Check if the game is over
        if game['state'] == 'Final':
            debug.info('GAME OVER')
            self.data.needs_refresh = False

    def _draw_post_game(self, game):
        # TEMP Open the logo image file
        away_team_logo = get_logo(game['away_team_abbrev'], self.height, self.data.config.helmet_logos)
        home_team_logo = get_logo(game['home_team_abbrev'], self.height, self.data.config.helmet_logos)

        # Flip home logo if using helmets
        if self.data.config.helmet_logos is True:
            home_team_logo = home_team_logo.transpose(Image.FLIP_LEFT_RIGHT)
            # Put the images on the canvas
            self.image.paste(away_team_logo, (round(-0.17 * self.width ), 0), mask=away_team_logo)
            self.image.paste(home_team_logo, (round(0.61 * self.width ), 0), mask=home_team_logo)

        else:
            # Put the images on the canvas
            if game['home_team_abbrev'] == "CGY":
                self.image.paste(home_team_logo, (round(0.505 * self.width), round(0.12 * self.height)), mask=home_team_logo)
            else:
                self.image.paste(home_team_logo, (round(0.585 * self.width), round(0.12 * self.height)), mask=home_team_logo)
            self.image.paste(away_team_logo, (round(-0.11 * self.width), round(0.12 * self.height)), mask=away_team_logo)

        # Prepare the data
        score = '{}-{}'.format(game['away_score'], game['home_score'])

        # Set the position of the information on screen.
        score_position = center_text(self.font.getlength(score), self.width / 2)
        # Draw the text on the Data image.
        self.draw.multiline_text((score_position, 0), score, fill=(255, 255, 255), font=self.font, align="center", stroke_width=1, stroke_fill=(0,0,0))
        self.draw.multiline_text((round(0.375 * self.width), round(0.38 * self.height)), "FINAL", fill=(255, 255, 255), font=self.font_mini,align="center", stroke_width=1, stroke_fill=(0,0,0))

        # Put the data on the canvas
        self.canvas.SetImage(self.image, 0, 0)

        # Load the canvas on screen.
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

        # Refresh the Data image.
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        self.data.needs_refresh = False

    def _draw_td(self):
        debug.info('TD')
        # Load the gif file
        ball = Image.open("assets/td_ball.gif")
        words = Image.open("assets/td_words.gif")
        if self.height == 64:
            ball = ball.resize(128, 64)
            words = words.resize(128, 64)
        # Set the frame index to 0
        frameNo = 0
        self.canvas.Clear()
        # Go through the frames
        x = 0
        while x != 3:
            try:
                ball.seek(frameNo)
            except EOFError:
                x += 1
                frameNo = 0
                ball.seek(frameNo)
            self.canvas.SetImage(ball.convert('RGB'), 0, 0)
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
            frameNo += 1
            t.sleep(0.05)
        x = 0
        while x != 3:
            try:
                words.seek(frameNo)
            except EOFError:
                x += 1
                frameNo = 0
                words.seek(frameNo)
            self.canvas.SetImage(words.convert('RGB'), 0, 0)
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
            frameNo += 1
            t.sleep(0.05)

    def _draw_fg(self):
        debug.info('FG')
        # Load the gif file
        im = Image.open("assets/fg.gif")
        if self.height == 64:
            im = im.resize(128, 64)
        # Set the frame index to 0
        frameNo = 0
        self.canvas.Clear()
        # Go through the frames
        x = 0
        while x != 3:
            try:
                im.seek(frameNo)
            except EOFError:
                x += 1
                frameNo = 0
                im.seek(frameNo)
            self.canvas.SetImage(im.convert('RGB'), 0, 0)
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
            frameNo += 1
            t.sleep(0.02)
