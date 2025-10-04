from PIL import Image, ImageDraw
from rgbmatrix import graphics
import math
import sys
import numpy as np
from utils import round_normal

DEBUG = False


class MatrixDrawer:
    """
    Core drawing functionality for matrices and buffers.
    Handles all drawing operations on a PIL image canvas.
    """

    def __init__(self, width, height, image=None, draw=None):
        """
        Initialize the drawer with a canvas.

        Args:
            width: Canvas width in pixels
            height: Canvas height in pixels
            image: Optional existing PIL Image (creates new if None)
            draw: Optional existing ImageDraw instance (creates new if None)
        """
        self.width = width
        self.height = height
        self.image = image or Image.new('RGBA', (self.width, self.height))
        self.draw = draw or ImageDraw.Draw(self.image)
        self.pixels = self.image.load()
        self.position_cache = {}

    def parse_location(self, value, dimension):
        """Check if number is percentage and calculate pixels"""
        if (isinstance(value, str) and value.endswith('%')):
            return round_normal((float(value[:-1]) / 100.0) * (dimension - 1))
        return value

    def align_position(self, align, position, size):
        """Calculate aligned position based on alignment string"""
        align = align.split("-")
        x, y = position

        # Handle percentages by converting to pixels
        x = self.parse_location(x, self.width)
        y = self.parse_location(y, self.height)

        if (align[0] == "center"):
            x -= size[0] / 2
        elif (align[0] == "right"):
            x -= size[0]

        if (len(align) > 1):
            if (align[1] == "center"):
                y -= size[1] / 2 + 1
            elif (align[1] == "bottom"):
                y -= size[1]

        if x % 2 == 0:
            x = math.ceil(x)
        else:
            x = math.floor(x)

        return (round_normal(x), round_normal(y))

    def draw_text(self, position, text, font, fill=None, align="left",
                backgroundColor=None, backgroundOffset=[1, 1, 1, 1]):
        """Draw text on the canvas"""
        width = 0
        height = 0
        text_chars = text.split("\n")
        offsets = []

        for index, chars in enumerate(text_chars):
            spacing = 0 if index == 0 else 1

            # This requires pillow V10.0.0 or greater
            left, top, right, bottom = font.getbbox(chars)
            offset_x = left
            offset_y = top - height - spacing

            offsets.append((offset_x, offset_y))

            bounding_box = font.getmask(chars).getbbox()
            if bounding_box is not None:
                width = bounding_box[2] if bounding_box[2] > width else width
                height += bounding_box[3] + spacing

        size = (width, height)
        x, y = self.align_position(align, position, size)

        if (backgroundColor is not None):
            self.draw_rectangle(
                (x - backgroundOffset[0], y - backgroundOffset[1]),
                (width + backgroundOffset[0] + backgroundOffset[2], height + backgroundOffset[1] + backgroundOffset[3]),
                backgroundColor
            )

        for index, chars in enumerate(text_chars):
            offset = offsets[index]
            chars_position = (x - offset[0], y - offset[1])
            self.draw.text(
                chars_position,
                chars,
                fill=fill,
                font=font
            )

        if (DEBUG):
            self.draw_pixel((x, y), (0, 255, 0))
            self.draw_pixel((x, y + height), (0, 255, 0))
            self.draw_pixel((x + width, y + height), (0, 255, 0))
            self.draw_pixel((x + width, y), (0, 255, 0))

        return {
            "position": (x, y),
            "size": size
        }

    def draw_image(self, position, image, align="left"):
        """Draw an image on the canvas"""
        position = self.align_position(align, position, image.size)

        try:
            self.image.paste(image, position, image)
        except Exception:
            self.image.paste(image, position)

        return {
            "position": position,
            "size": image.size
        }

    def draw_rectangle(self, position, size, fill=None, outline=None):
        """Draw a rectangle on the canvas"""
        x, y = position
        width, height = size
        draw = ImageDraw.Draw(self.image)

        # Calculate bottom-right corner from position and size
        right = x + width - 1
        bottom = y + height - 1

        # Draw rectangle [(left, top), (right, bottom)]
        draw.rectangle([(x, y), (right, bottom)], fill=fill, outline=outline)

        return {
            "position": (x, y),
            "size": size
        }

    def draw_pixel(self, position, color):
        """Draw a single pixel"""
        try:
            self.pixels[position] = color
        except Exception:
            print(position, "out of range!")

    def draw_pixels(self, position, pixels, size, align="left"):
        """Draw multiple pixels"""
        x, y = self.align_position(align, position, size)

        for pixel in pixels:
            self.draw_pixel(
                (
                    pixel.position[0] + x,
                    pixel.position[1] + y,
                ),
                pixel.color
            )

    def draw_text_layout(
        self,
        layout,
        text,
        align="left",
        fillColor=None,
        backgroundColor=None,
        backgroundOffset=[1, 1, 1, 1]
    ):
        """Draw text using layout configuration"""
        if fillColor is None:
            fillColor = layout.color
        self.cache_position(
            layout.id,
            self.draw_text(
                self.layout_position(layout),
                text,
                fill=fillColor,
                font=layout.font,
                backgroundColor=backgroundColor,
                backgroundOffset=backgroundOffset,
                align=layout.align
            )
        )

    def draw_image_layout(self, layout, image, offset=(0, 0)):
        """Draw image using layout configuration"""
        self.cache_position(
            layout.id,
            self.draw_image(
                self.layout_position(layout, offset),
                image,
                layout.align
            )
        )

    def draw_pixels_layout(self, layout, pixels, size):
        """Draw pixels using layout configuration"""
        self.cache_position(
            layout.id,
            self.draw_pixels(
                self.layout_position(layout),
                pixels,
                size,
                layout.align
            )
        )

    def draw_rectangle_layout(self, layout, fillColor=None, outline=None):
        """Draw rectangle using layout configuration"""
        size = (layout.size[0], layout.size[1])
        self.cache_position(
            layout.id,
            self.draw_rectangle(
                self.layout_position(layout),
                size, fill=fillColor, outline=outline)
        )

    def layout_position(self, layout, offset=(0, 0)):
        """Calculate position from layout with relative positioning support"""
        x = layout.position[0] + offset[0]
        y = layout.position[1] + offset[1]

        if (hasattr(layout, 'relative') and layout.relative.to in self.position_cache):
            cached_position = self.position_cache[layout.relative.to]
            position = self.align_position(
                layout.relative.align,
                cached_position["position"],
                (
                    -cached_position["size"][0],
                    -cached_position["size"][1]
                )
            )

            x += position[0]
            y += position[1]

        return (x, y)

    def cache_position(self, id, position):
        """Cache a position for relative layout positioning"""
        self.position_cache[id] = position

    def get_text_center_position(self, text, font, y_pos):
        """Get the x,y coordinates to center text horizontally at given y position"""
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        x_pos = (self.width - text_width) // 2
        return (x_pos, y_pos)

    def draw_text_centered(self, y_pos, text, font, fill=None, backgroundColor=None):
        """Draw text centered horizontally at given y position"""
        pos = self.get_text_center_position(text, font, y_pos)
        self.draw_text(pos, text, font=font, fill=fill, backgroundColor=backgroundColor)


class Matrix:
    def __init__(self, matrix):
        self.matrix = matrix
        self.graphics = graphics
        self.brightness = None

        # Create a new data image.
        self.width = matrix.width
        self.height = matrix.height

        # Use MatrixDrawer for all drawing operations
        self.drawer = MatrixDrawer(self.width, self.height)

        # Expose common properties for backward compatibility
        self.image = self.drawer.image
        self.draw = self.drawer.draw
        self.pixels = self.drawer.pixels
        self.position_cache = self.drawer.position_cache

        self.use_canvas = False

        if (self.use_canvas):
            self.canvas = matrix.CreateFrameCanvas()

    def create_offscreen_buffer(self, width=None, height=None):
        """
        Create an offscreen buffer (larger canvas) for rendering scrollable content.
        Returns a new OffscreenBuffer object that can use all the same drawing methods,
        but renders to a larger image that can be scrolled.

        Args:
            width: Width of buffer (defaults to matrix width)
            height: Height of buffer (required for offscreen rendering)

        Returns:
            OffscreenBuffer object with same drawing interface as Matrix

        Example:
            buffer = matrix.create_offscreen_buffer(height=80)
            buffer.draw_text_layout(layout.header, "TITLE")
            scrolling_image = buffer.get_image()
            # Then scroll the image using matrix.draw_image() with different y offsets
        """
        if height is None:
            raise ValueError("height parameter is required for offscreen buffer")

        return OffscreenBuffer(self, width or self.width, height)

    def set_brightness(self, brightness):
        self.brightness = brightness
        self.matrix.brightness = self.brightness

    # Delegate all drawing methods to MatrixDrawer
    def parse_location(self, value, dimension):
        return self.drawer.parse_location(value, dimension)

    def align_position(self, align, position, size):
        return self.drawer.align_position(align, position, size)

    def draw_text(self, position, text, font, fill=None, align="left",
                backgroundColor=None, backgroundOffset=[1, 1, 1, 1]):
        return self.drawer.draw_text(position, text, font, fill, align, backgroundColor, backgroundOffset)

    def draw_image(self, position, image, align="left"):
        return self.drawer.draw_image(position, image, align)

    def draw_rectangle(self, position, size, fill=None, outline=None):
        return self.drawer.draw_rectangle(position, size, fill, outline)

    def draw_pixel(self, position, color):
        return self.drawer.draw_pixel(position, color)

    def draw_pixels(self, position, pixels, size, align="left"):
        return self.drawer.draw_pixels(position, pixels, size, align)

    def draw_text_layout(
        self,
        layout,
        text,
        align="left",
        fillColor=None,
        backgroundColor=None,
        backgroundOffset=[1, 1, 1, 1]
    ):
        return self.drawer.draw_text_layout(layout, text, align, fillColor, backgroundColor, backgroundOffset)

    def draw_image_layout(self, layout, image, offset=(0, 0)):
        return self.drawer.draw_image_layout(layout, image, offset)

    def draw_pixels_layout(self, layout, pixels, size):
        return self.drawer.draw_pixels_layout(layout, pixels, size)

    def draw_rectangle_layout(self, layout, fillColor=None, outline=None):
        return self.drawer.draw_rectangle_layout(layout, fillColor, outline)

    def layout_position(self, layout, offset=(0, 0)):
        return self.drawer.layout_position(layout, offset)

    def cache_position(self, id, position):
        return self.drawer.cache_position(id, position)

    def render(self):
        if (DEBUG):
            for x in range(self.height):
                self.draw_pixel(
                    (self.width / 2 - 1, x),
                    (0, 255, 0)
                )
                self.draw_pixel(
                    (self.width / 2, x),
                    (0, 255, 0)
                )

            for x in range(self.width):
                self.draw_pixel(
                    (x, self.height / 2 - 1),
                    (0, 255, 0)
                )
                self.draw_pixel(
                    (x, self.height / 2),
                    (0, 255, 0)
                )

        if (self.use_canvas):
            self.canvas.SetImage(self.image.convert('RGB'), 0, 0)
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
        else:
            self.matrix.SetImage(self.image.convert('RGB'))

    def clear(self):
        self.image.paste(0, (0, 0, self.width, self.height))

    def network_issue_indicator(self):
        red = self.graphics.Color(255, 0, 0)
        self.graphics.DrawLine(self.matrix, 0, self.matrix.height - 1, self.matrix.width, self.matrix.height - 1, red)

    def update_indicator(self):
        green = self.graphics.Color(0, 255, 0)
        self.graphics.DrawLine(self.matrix, 0, 0, self.matrix.width,0, green)

    def get_text_center_position(self, text, font, y_pos):
        return self.drawer.get_text_center_position(text, font, y_pos)

    def draw_text_centered(self, y_pos, text, font, fill=None, backgroundColor=None):
        return self.drawer.draw_text_centered(y_pos, text, font, fill, backgroundColor)


class OffscreenBuffer:
    """
    An offscreen rendering buffer that provides the same drawing interface as Matrix
    but renders to a larger canvas for scrolling content.
    """

    def __init__(self, parent_matrix, width, height):
        """
        Initialize offscreen buffer.

        Args:
            parent_matrix: The parent Matrix instance
            width: Width of the buffer
            height: Height of the buffer
        """
        self.parent_matrix = parent_matrix
        self.width = width
        self.height = height
        self.graphics = parent_matrix.graphics

        # Use MatrixDrawer for all drawing operations
        self.drawer = MatrixDrawer(self.width, self.height)

        # Expose common properties for backward compatibility
        self.image = self.drawer.image
        self.draw = self.drawer.draw
        self.pixels = self.drawer.pixels
        self.position_cache = self.drawer.position_cache

    def get_image(self):
        """Return the rendered image for scrolling."""
        return self.drawer.image

    # Delegate all drawing methods to MatrixDrawer
    def parse_location(self, value, dimension):
        return self.drawer.parse_location(value, dimension)

    def align_position(self, align, position, size):
        return self.drawer.align_position(align, position, size)

    def draw_text(self, position, text, font, fill=None, align="left",
                backgroundColor=None, backgroundOffset=[1, 1, 1, 1]):
        return self.drawer.draw_text(position, text, font, fill, align, backgroundColor, backgroundOffset)

    def draw_image(self, position, image, align="left"):
        return self.drawer.draw_image(position, image, align)

    def draw_rectangle(self, position, size, fill=None, outline=None):
        return self.drawer.draw_rectangle(position, size, fill, outline)

    def draw_pixel(self, position, color):
        return self.drawer.draw_pixel(position, color)

    def draw_pixels(self, position, pixels, size, align="left"):
        return self.drawer.draw_pixels(position, pixels, size, align)

    def draw_text_layout(self, layout, text, align="left", fillColor=None, backgroundColor=None, backgroundOffset=[1, 1, 1, 1]):
        return self.drawer.draw_text_layout(layout, text, align, fillColor, backgroundColor, backgroundOffset)

    def draw_image_layout(self, layout, image, offset=(0, 0)):
        return self.drawer.draw_image_layout(layout, image, offset)

    def draw_pixels_layout(self, layout, pixels, size):
        return self.drawer.draw_pixels_layout(layout, pixels, size)

    def draw_rectangle_layout(self, layout, fillColor=None, outline=None):
        return self.drawer.draw_rectangle_layout(layout, fillColor, outline)

    def layout_position(self, layout, offset=(0, 0)):
        return self.drawer.layout_position(layout, offset)

    def cache_position(self, id, position):
        return self.drawer.cache_position(id, position)

    def get_text_center_position(self, text, font, y_pos):
        return self.drawer.get_text_center_position(text, font, y_pos)

    def draw_text_centered(self, y_pos, text, font, fill=None, backgroundColor=None):
        return self.drawer.draw_text_centered(y_pos, text, font, fill, backgroundColor)


class MatrixPixels:
    def __init__(self, position, color):
        self.position = position
        self.color = color


def get_ansi_color_code(r, g, b):
    if r == g and g == b:
        if r < 8:
            return 16
        if r > 248:
            return 231
        return round(((r - 8) / 247) * 24) + 232
    return 16 + (36 * round(r / 255 * 5)) + (6 * round(g / 255 * 5)) + round(b / 255 * 5)


def get_color(r, g, b):
    return "\x1b[48;5;{}m \x1b[0m".format(int(get_ansi_color_code(r,g,b)))


def show_image(img):
    h = img.height
    w = img.width

    # Get image
    img = img.resize((w,h), Image.ANTIALIAS)
    # Set to array
    img_arr = np.asarray(img)
    # Get the shape so we know x,y coords
    h,w,c = img_arr.shape

    # Then draw our mona lisa
    mona_lisa = ''
    for x in range(h):
        for y in range(w):
            pix = img_arr[x][y]
            color = ' '
            # 90% of our image is black, and the pi sometimes has trouble writing to the terminal
            # quickly. So default the color to blank, and only fill in the color if it's not black
            if sum(pix) > 0:
                color = get_color(pix[0], pix[1], pix[2])
            mona_lisa += color
    sys.stdout.write(mona_lisa)
    sys.stdout.flush()
