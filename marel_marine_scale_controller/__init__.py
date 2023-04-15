import os, sys

VERSION = "1.0.0"

PROGRAM_DIRECTORY = os.path.dirname(__file__)

LUA_SCRIPT_PATH = os.path.join(PROGRAM_DIRECTORY, "static/marel_app.lua")
CONFIG_PATH = os.path.join(PROGRAM_DIRECTORY, "config/gui_config.json")
LOGO_PATH = os.path.join(PROGRAM_DIRECTORY, "static/logo.ico")


COMM_PORT = 52212
DOWNLOAD_PORT = 52202
UPLOAD_PORT = 52203
