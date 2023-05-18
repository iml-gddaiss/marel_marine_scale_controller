import logging
from pathlib import Path
from marel_marine_scale_controller import LUA_SCRIPT_PATH, CONFIG_PATH, LOGO_PATH
from marel_marine_scale_controller.gui import GUI

PROGRAM_DIRECTORY = Path(__file__).parent

ABS_LUA_SCRIPT_PATH = str(PROGRAM_DIRECTORY.joinpath(LUA_SCRIPT_PATH))
ABS_CONFIG_PATH = str(PROGRAM_DIRECTORY.joinpath(CONFIG_PATH))
ABS_LOGO_PATH = str(PROGRAM_DIRECTORY.joinpath(LOGO_PATH))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    gui = GUI(lua_script_path=ABS_LUA_SCRIPT_PATH, config_path=ABS_CONFIG_PATH, logo_path=ABS_LOGO_PATH)
    gui.run()
