import json
import os
from utils import get_file
import debug

from . import config_models
from pydantic import ValidationError


class ScoreboardConfig:
    try:
        def __init__(self, filename_base, args):
            input_json = self.__get_config(filename_base)
            config = config_models.ConfigModel.model_validate(input_json)

            # Preferred Teams
            self.preferred_teams = config.preferred_teams

            # Logo Selection
            self.helmet_logos = config.helmet_logos

            # Rotation
            self.rotation_enabled = config.rotation.enabled
            self.rotation_only_preferred = config.rotation.only_preferred
            self.rotation_rates = config.rotation.rates.model_dump()
            self.rotation_preferred_team_live_enabled = config.rotation.while_preferred_team_live
            self.rotation_preferred_team_live_halftime = config.rotation.while_preferred_team_halftime

            # Refresh Rate
            self.data_refresh_rate = config.data_refresh_rate

            # Debug
            self.debug = config.debug
            self.testing = config.testing

            # Rotation Settings
            self.rotation_rates = config.rotation.rates
            self.rotation_rates_pregame = self.rotation_rates.pregame
            self.rotation_rates_live = self.rotation_rates.live
            self.rotation_rates_final = self.rotation_rates.final

        def read_json(self, filename):
            # Find and return a json file
            output = {}
            path = get_file(filename)
            if os.path.isfile(path):
                with open(path, encoding='utf-8') as output_file:
                    output = json.load(output_file)
                    output_file.close()
            return output

        def __get_config(self, base_filename):
            # Look and return config.json file
            filename = f"{base_filename}.json"
            reference_config = self.read_json(filename)

            return reference_config

    except ValidationError as e:
        debug.error(e)
