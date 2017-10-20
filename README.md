# DragonflyOps_clients
Python-based client example library and mapper for DragonflyOps game

Clients can be made in any language or environment that supports TCP sockets to your localhost. These examples are in Python.

## Library: client_base.py
A python-based library containing some utilities for connecting to the server and working with the JSON data responses.
It includes a simple keyboard input function and a class that sketches some data structures for helping the player store map location data in the game (exemplified in mpl_mapper.py).

## Mapping tool: mpl_mapper.py
*Requires matplotlib library* ([free install of scientific python environment](http://www.anaconda.com))

 - Best run inside a console Jupyter session, this script can be run once a drone is deployed, when it will bring up a
matplotlib plot window containing a "graph"-like map of locations visited.
 - The drone's current location is marked in green.
 - Directional navigation is possible using "n", "s", "e", "w" key entries followed by <RETURN>. These commands will always run a scan on arrival
in a new room location. Use the underlying "!M<direction>" commands to avoid this if you prefer.
 - All regular console game commands are available too.
 - Command "x" marks the current location on the map with a check mark and "r" marks it red. These are toggles,
so repeating the command at the location will remove the marking. Use these to keep note of special locations.

## Bot tool: random_walker.py
This is a very early and incomplete prototype of a bot that crawls the map. It is not yet able to work with doors. You could adapt this code to hand off door actions to the user or
set up the command pattern to automate it. But you'll have to be smart about what to do for doors requiring authentication! Has the bot found the right keycode yet?
