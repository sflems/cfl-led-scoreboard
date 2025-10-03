import sys
from data.cfl_api.scoreboard_config import ScoreboardConfig
from data.cfl_api.data import Data
from renderer.main import MainRenderer
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from utils import args, led_matrix_options
import logging
import debug
from rich.logging import RichHandler
from rich.traceback import install
install(show_locals=True) 


SCRIPT_NAME = "CFL Scoreboard"
SCRIPT_VERSION = "1.0.0"

# Initialize the logger with default settings
debug.setup_logger()
sb_logger = logging.getLogger("cfl-scoreboard")

def run():
      # Get supplied command line arguments
      commandArgs = args()


      # Check for led configuration arguments
      matrixOptions = led_matrix_options(commandArgs)
      matrixOptions.drop_privileges = False

      # Read scoreboard options from config.json if it exists
      config = ScoreboardConfig("config", commandArgs)

      #If we pass the logging arguments on command line, override what's in the config.json, else use what's in config.json (color will always be false in config.json)
      if commandArgs.loglevel is not None:
            debug.set_debug_status(config, loglevel=commandArgs.loglevel)
      else:
            debug.set_debug_status(config, loglevel=config.loglevel)

      # Initialize the matrix
      matrix = RGBMatrix(options=matrixOptions)

      # Print some basic info on startup
      sb_logger.info("{} - v{} ({}x{})".format(SCRIPT_NAME, SCRIPT_VERSION, matrix.width, matrix.height))

    # This data will get passed throughout the entirety of this program.
    # It initializes all sorts of things like current season, teams, helper functions
      data = Data(config)

      # Initialize the  Renderer
      MainRenderer(matrix, data).render()

if __name__ == "__main__":
    try:
        run()

    except KeyboardInterrupt:
        print("Exiting CFL-LED-SCOREBOARD\n")
        # sb_cache.close() # TODO
        sys.exit(0)