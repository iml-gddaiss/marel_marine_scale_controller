import os, sys
from pathlib import Path

VERSION = "1.0.0"

PROGRAM_DIRECTORY = Path(__file__).parent

LUA_SCRIPT_PATH = str(PROGRAM_DIRECTORY.joinpath("static/marel_app.lua"))
CONFIG_PATH = str(PROGRAM_DIRECTORY.joinpath("config/gui_config.json"))
LOGO_PATH = str(PROGRAM_DIRECTORY.joinpath("static/logo.ico"))


COMM_PORT = 52212
DOWNLOAD_PORT = 52202
UPLOAD_PORT = 52203
