# marel_marine_scale_controller
Python Controller and Lua application for Marel Marine Scale M2200. 
The GUI application will essentially turn a Marel Marine Scale into a keyboard.

Note that this project was developed with the Marel Marine Scale M2200. Therefor, there are no guarantees that it will work with other models.


# Description

# Download

The GUI App is packaged as standalone executable for Windows and Linux.


For Windows:
1. Download from the latest release [here](https://github.com/iml-gddaiss/marel_marine_scale_controller/releases) 
2. Unzip `marel_marine_scale_app-windows.zip`
3. Run `marel_marine_scale_app.exe`

# Package requirements
+ Python >= 3.10

# Usage

## Scale

(Default Service Password: 62735)
(Default W&M Config password: 322225)

The `Page` key:
<p align='center'>
<img src='docs/images/page_button.png' width='66' alt="Scale main display"/>
</p>

 
+ Press the `Page` key to browse through the pages and to exit pages.
+ Hold the `Page` to access the scale menu.

The follow options are required in order to use the Python Application: 

From the Menu page go to options page,

`4-System Settings -> System -> Configuration -> Options`,

then set the following: 

+ Select top menu cycle : 2-Application [x]
+ Allow Lua source update : Yes
+ Run Lua script : Yes

... set packing (?) TODO

## Scale Lua Application

<p align='center'>
<img src='docs/images/marel_main_annotated.png' width='600' alt="Scale main display"/>
</p>

While program 1 is running, weight values are continuously sent to the controller. (e.i. `%w,1.234kg#\n`)

<p align='center'>
<img src='docs/images/marel_prog_1.jpg' width='600' alt="Scale prog 1 display"/>
</p>

Pressing the `Print` key sends a print message to the python controller. (e.i. `%p,1.234kg#\n`) (see section [Additional Information/Lua Script](#lua-script))

<p align='center'>
<img src='docs/images/marel_sent.jpg' width='600' alt="Scale sent display"/>
</p>

When a print message is sent the screen will display this message: `>>>> SENT <<<<`

## GUI Python Application
<p align='center'>
<img src='docs/images/marel_gui_annoted.png' width='2' alt="Python gui app" />
</p>

On first usage, the Lua Script needs to be uploaded to the scale. This can be done even when the app is not connected to the scale. 


# Additional Information
## About the Marel Marine Scale M2200
The Marel [documentation](./docs/marel_marine_m2200_user_guide.pdf) doesn't really tell you how to connect to and interact with the scale. The following explanation is thus mostly empirical. 

The scale has an empty Lua file in its memory. This file can be overwritten by uploading a Lua files to the scale. 
Then, if the scale (parameter](TODO: Add to Guide) "Run Lua Script" is `On`, the script is run in loop by a Lua interpreter.
IMPORTANT: It seems that a new Lua Interpreter is launch each time, thus the Lua Script should itself be looping to avoid closing and opening new interpreters which cost time.
Also, if a new Lua script is uploaded to the scale, it will only be run when a new Lua interpreter is started, thus if one is already running, it needs to be closed. 

The scale has 7 different tcp servers ports for communication, from the documentation we have:

+ 52200 dot commands
+ 52202 download Lua source, if allowed 
+ 52203 upload Lua source
+ 52210 Lua standard output, for example using Lua print()
+ 52211 message port “comm4” in Lua, persistent output queue
+ 52212 terminal port “comm5” in Lua
+ 52213 remote host port “comm6” in Lua 

Note:
- The Lua Script is uploaded via the `52202` download port, and downloaded form the `52203` upload port.
- The port `52211`, `52212` and `52213` can be use has Communications port.


While it seems that some of the "built-in" Lua functions are missing from the Lua interpreter (however I might be wrong here),
the Marel [documentation](./docs/marel_marine_m2200_user_guide.pdf) provides a list of available Lua functions with to interface with the scale and manipulate strings.
Using the Marel [documentation](./docs/marel_marine_m2200_user_guide.pdf) and the Lua script to be used with the Python app ([marel_app_v2.lua](marel_marine_scale_controller/static/marel_app_v2.lua)), one could make their own Lua Sript for the Scale.



## Lua Script:
Apart from the graphical user interface on the Sreen #2 of the scale (see section [Usage/Scale](#scale)), 
the [Lua application](marel_marine_scale_controller/static/marel_app_v2.lua) is used to send weight measurements over the ethernet communication port `5`(`52212`).
The messages format is as follows `%<prefix>,<weight><units>#\n`, where:
```
    prefix: `"w"` or `"p"`.
    weight: float of variable precision.
    units: Unit of the weight `("kg", "g", "lb", "oz")`.
```
e.g. `%w,1.234kg#\n`
Messages with the prefix `"w"` are sent at regular intervals while `"p"` messages are sent when the assign [key](TODO) on the Scale is pressed.
When receiving `"p"` messages, the Controller emulates a keyboard entry of that given values.


## The Python Controller 

The controller is used to:
    - Connect ot the Marel Scale via Ethernet.
    - Upload the Compatible Lua Application to the scale.
    - Store the latest weight value and units.
    - Print the latest received weight value in a given units at the current cursor position. (Keyboard Emulation)
