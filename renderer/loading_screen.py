import os
from PIL import Image, ImageFont, ImageDraw


PATH = "assets/"
VERSION_FONT = ImageFont.truetype("assets/fonts/VGA.ttf", 12)
VERSION_FONT_64 = ImageFont.truetype("assets/fonts/04B_24__.TTF", 8)

class Loading:
    def __init__(self, matrix,__version__):
        self.matrix = matrix
        self.version = __version__

	# Check to see if loading image for screen size exists, if not, fall back to 
        # original 64x32 one
      
        #img = f"{PATH}/fg-{self.matrix.width}x{self.matrix.height}.gif"
        img_ori = f"{PATH}/fg.gif"

    #if os.path.exists(img):
    #   self.image = Image.open(img)
    #else:
        self.image = Image.open(img_ori)
        self.image.resize((128, 64))

    def render(self):

        if self.matrix.width > 64:
            self.matrix.draw_image(
                (3,3),
                self.image
            )
        else:
            self.matrix.draw_image(
                (4,2),
                self.image)
        
        
        if self.matrix.width > 64:
            self.matrix.draw_text(["3%","3%"], f"V{self.version}", VERSION_FONT)
        else:
            self.matrix.draw_text(["2%","2%"], f"V{self.version}", VERSION_FONT_64)
        
        self.matrix.render()