from data.cfl_api.data import Data
from data.cfl_api.scoreboard_config import ScoreboardConfig
from renderer.main import MainRenderer
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from utils import args, led_matrix_options
import debug

SCRIPT_NAME = "CFL Scoreboard"
SCRIPT_VERSION = "1.0.0"

# Get supplied command line arguments
args = args()

# Read scoreboard options from config.json if it exists

config = ScoreboardConfig("config", args)
#If we pass the logging arguments on command line, override what's in the config.json, else use what's in config.json (color will always be false in config.json)
if args.logcolor and args.loglevel is not None:
      debug.set_debug_status(config.debug, logcolor=args.logcolor, loglevel=args.loglevel)
elif not args.logcolor and args.loglevel is not None:
      debug.set_debug_status(config.debug, loglevel=args.loglevel)
elif args.logcolor and args.loglevel is None:
      debug.set_debug_status(config.debug, logcolor=args.logcolor, loglevel=config.loglevel)
else:
      debug.set_debug_status(config.debug, loglevel=config.loglevel)
      
# Check for led configuration arguments
matrixOptions = led_matrix_options(args)

# Initialize the matrix
matrix = RGBMatrix(options=matrixOptions)

# Print some basic info on startup
debug.info("{} - v{} ({}x{})".format(SCRIPT_NAME, SCRIPT_VERSION, matrix.width, matrix.height))

# Initialize the config & Renderer
data = Data(config)
MainRenderer(matrix, data).render()
