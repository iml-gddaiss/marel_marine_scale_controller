# marel_marine_scale_controller
Python Controller and Lua application for Marel Marine Scale M2200.

# Description

# Download

The App is packaged as standalone executable for Windows and Linux.
Download [here](https://github.com/iml-gddaiss/marel_marine_scale_controller/releases)

# Usage


# Marel Marine Scale M2200


# Controller 
The controller is used to:
    - Connect ot the Marel Scale via Ethernet.
    - Upload the Compatible Lua Application to the scale.
    - Store the latest weight values.
    - Print received weight values at the current cursor position. (Keyboard Emulation)


# Lua application:
The Lua application developed for the Scale (`./static/marel_app_v2.lua`) sends messages of the form:
```
    %<prefix>,<weight><units>#\n
```
where:

    prefix: `"w"` or `"k"`.
    weight: float of variable precision.
    units: Unit of the weight `("kg", "g", "lb", "oz")`.
Messages with the prefix `"w"` are sent at regular intervals while `"k"` messages are sent when the assign button on the Scale is pressed.
When receiving `"k"` messages, the Controller emulates a keyboard entry of that given values.
The Lua application also adds a simple interface on the Scale's screen #2.

## Lua Application Usage
