from PIL import Image, ImageFont, ImageDraw
import logging

debug = logging.getLogger('cfl-scoreboard')

VERSION_FONT = ImageFont.truetype("assets/fonts/VGA.ttf", 12)
VERSION_FONT_64 = ImageFont.truetype("assets/fonts/04B_24__.TTF", 8)

class Loading:
    def __init__(self, matrix, __version__, sleepEvent):
        self.matrix = matrix
        self.version = __version__
        self.sleepEvent = sleepEvent

    def render(self):
        debug.info('LOADING CFL SCOREBOARD')
        self.play_gif()

            
    def play_gif(self):
        im = Image.open("assets/td_ball.gif")

        # Set the frame index to 0
        frame_nub = 0
        # Set number of loop to 1 (if you want to play you animation more then once, change this variable)
        numloop = 2
        self.matrix.clear()

        # Go through the frames
        x = 0
        while x is not numloop:
            try:
                im.seek(frame_nub)
            except EOFError:
                x += 1
                if x == numloop:
                    return
                frame_nub = 0
                im.seek(frame_nub)

            self.matrix.draw_image(("50%", 0), im, "center")

                
            if self.matrix.width > 64:
                self.matrix.draw_text_centered("3%", f"V{self.version}", VERSION_FONT)
            else:
                self.matrix.draw_text_centered("2%", f"V{self.version}", VERSION_FONT_64)
                
            self.matrix.render()
            
            frame_nub += 1
            self.sleepEvent.wait(0.1)
