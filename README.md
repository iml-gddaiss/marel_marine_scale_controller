# marel_marine_scale_controller
Python Controller and Lua application for Marel Marine Scale M2200. 
The GUI application will essentially turn a Marel Marine Scale M2200 into a keyboard.

Note that this project was developed with the Marel Marine Scale M2200. Therefore, there are no guarantees that it will work with other models.

# Table of Content

1. [Download](#download)
2. [Requirements](#requirements)
3. [Usage](#usage) 
   * 3.1 [Marel Marine Scale M2202](#marel-marine-scale-m2200)
   * 3.2 [Lua Application](#scale-lua-application)
   * 3.3 [Python Application](#python-application)
4. [Additionnal information](#additional-information)

# Download

The GUI App is packaged as standalone (self-contained) executable for Windows and Linux.


For Windows:
1. Download from the latest release [here](https://github.com/iml-gddaiss/marel_marine_scale_controller/releases) 
2. Unzip `marel_marine_scale_app-windows.zip`
3. Run `marel_marine_scale_app.exe`

# Requirements

+ Python >= 3.10

# Usage

## Marel Marine Scale M2200

[//]: # (From the Marel [documentation]&#40;./docs/marel_marine_m2200_user_guide.pdf&#41; )

`(Default Service Password: 62735)`

`(Default W&M Config password: 322225)`

The `Page` key:
<p align='center'>
<img src='docs/images/page_button.png' width='66' alt="Scale main display"/>
</p>

 
+ Press the `Page` key to browse through the pages and to exit pages.
+ Hold the `Page` to access the scale menu fom which you can access the different pages (screens). 

The follow settings options are required in order to use the Scale with the Python Application.
From the Menu page: go to options page,

+ `4-System Setup -> System -> Configuration -> Options`
  + `Select top menu cycle` : `2-Application [Yes]`
  + `Allow Lua source update` : `Yes`
  + `Run Lua script` : `Yes`

For the `Packing`, see page 13 of [documentation](./docs/marel_marine_m2200_user_guide.pdf)
(TODO tester les differents Packing.)
+ `4-System Setup -> System -> Settings`
  + `Packing` : `Nominal weight`




## Scale Lua Application

**Note** On first usage, the Lua Script needs to be uploaded to the scale. see section [Python Application](#python-application) 


The Lua Application is displayed on screen #2, the `2-Application` page in the page menu.

<p align='center'>
<img src='docs/images/marel_main_annotated.png' width='600' alt="Scale main display"/>
</p>

While program 1 is running, weight values are continuously sent (e.i. `%w,1.234kg#\n`, see section [Additional Information/Lua Script](#lua-script)).
The Python Application stores the latest values and the GUI displays it.

<p align='center'>
<img src='docs/images/marel_prog_1.jpg' width='600' alt="Scale prog 1 display"/>
</p>

Pressing the `Print` key sends a print message (e.i. `%p,1.234kg#\n`, see section [Additional Information/Lua Script](#lua-script)).
When receiving a `Print` messages, the Python Application emulates a keyboard entry of that given values.


<p align='center'>
<img src='docs/images/marel_sent.jpg' width='600' alt="Scale sent display"/>
</p>

When a print message is sent the screen will display this message: `>>>> SENT <<<<`

## Python Application

The [GUI](marel_marine_scale_controller/gui.py) is used to interface with the [Controller](marel_marine_scale_controller/marel_controller.py) which is used to:

### The Controller
#### Create a Controller
```Python
>>> from marel_marine_scale_controller.marel_controller import MarelController
>>> controller = MarelController('host')
```

#### Connect the Controller (via ethernet) and start Listening
```Python
>>> controller.start_listening()
```
When listening, the controller:

- Stores the latest weight value and units (message prefixes `w` and `p`).
- Prints the latest received weight in a given units at the current cursor position (message prefix `p`).

#### Upload the compatible Lua Script to the Marel Scale
```Python
>>> controller.update_lua_code('path/to/script.lua')
```

#### Get the latest weight value
```Python
>>> controller.get_weight(units='kg')
```

### The GUI
<p align='center'>
<img src='docs/images/marel_gui_annotated.png' width='1000' alt="Python gui app" />
</p>

**Note** The `Update Lua App` function doesn't require the App to be Connected since it uses different ports.


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
+ 52212 terminal port “comm5” in Luae
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
