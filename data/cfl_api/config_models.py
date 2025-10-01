from __future__ import annotations
from typing import FrozenSet
from enum import Enum
from pydantic import ConfigDict, BaseModel, Field


class Rates(BaseModel):
    pregame: float = Field(..., ge=2,
                           description="Sets pre-game rotation rate. (Min=2.0)")
    live: float = Field(..., ge=2,
                        description="Sets live-game rotation rate. (Min=2.0)")
    final: float = Field(..., ge=2,
                         description="Sets post-game rotation rate. (Min=2.0)")


class Rotation(BaseModel):
    enabled: bool = Field(..., description="Enable rotation of games.")
    only_preferred: bool = Field(...,
                                 description="Rotate only preferred teams.")
    rates: Rates
    while_preferred_team_live: bool = Field(
        ..., description="Rotate games while preferred team is live.")
    while_preferred_team_halftime: bool = Field(
        ..., description="Rotate games while preferred teams is at halftime.")


class Team(str, Enum):
    """
    CFL Teams
    """
    BC = "BC"
    CGY = "CGY"
    EDM = "EDM"
    HAM = "HAM"
    MTL = "MTL"
    OTT = "OTT"
    SSK = "SSK"
    TOR = "TOR"
    WPG = "WPG"


class ConfigModel(BaseModel):
    preferred_teams: FrozenSet[Team] = Field(..., title="Preferred Teams",
                                        description="List of preferred teams to display. First is priority.")
    rotation: Rotation
    helmet_logos: bool = Field(
        default=False,
        title="Helmet Logos",
        description="Enable helmet logos.")
    data_refresh_rate: float = Field(...,
                                     ge=5, description="Sets refresh rate for games data. Overrides rotation rates to limit requests* (Min=5.0)")
    debug: bool = Field(default=False, description="Enable debugging.")
    testing: bool = Field(default=False, description="Enabled test data.")
    model_config = ConfigDict(title='CFL LED Scoreboard Config Schema', use_enum_values=True)
