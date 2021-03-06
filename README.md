# Blendorf: A 3D visualisation tool for Dwarf Fortress using Blender

## Project Vision and scope

Blendorf aims to be a highly customisable 3D visualiser for exported Dwarf Fortress maps.

The following features sets it apart from other visualisers:
- easy customisability of the art assets
- easily edit the generated map
- make raytraced renders of your fortress
- terrain that makes sense in the context of the game
	
It is supposed to enable the user to explore and show off his/her fortress and create art based on the game.
The customisability of the terrain itself will be rather limited but textures and models for shrubs, animals etc. can be changed easily.

## Current Status and TODOs/planned features

Blendorf is currently far from being in a state that could be described as completed.
* It only works with Dwarf Fortress 0.34.11 and earlier because they had the mapexport plugin for DFHack, which has not been updated for the Dwarf Fortress 0.40.XX versions. It's probably easiest to use the DFHack lua script interface to make a mapexport script.
* The terrain generation is declared finished for 0.34.11 maps. Trees and shrubs are preliminary and will be updated with the availability of 0.40.XX maps. Liquids are not implemented yet.
* Dummy materials are present for all the 0.34 materials. They should have some settings that are simple but look decent (textures like Minecraft might work).
* Including buildings and units is planned, but first needs a way to export the information to a Blender-readable format (probably a script similar to mapexport).
	
## Usage/Installation

Once the project is in a release-ready state I will try to make a downloadable package that includes all necessary files and is easy-to-use.
For now, my current setup and procedure is described below. It may be possible to change some things about this, but I haven't tried anything.

Installed programs:
* Blender v2.72b; rename or remove the python folder in the Blender installation folder so that the packaged python isn't used
* Python v3.4.2 installation
* Google protobuf for Python 3 https://pypi.python.org/packages/source/p/protobuf-py3/protobuf-py3-2.5.1-pre.tar.gz
	
Procedure:
- open the template_oct.blend file directly from the code folder (not from inside Blender)
- in the info panel go to Window > Toggle System Console
- in the Text Editor panel go to Text > Run Script (Alt + P)
	
Note that terrain generation can take a few minutes. Having very large maps will lead to Blender lagging unless you have a powerful PC. Use the min and max coordinate settings in script_from_pydata.py 
The generated 3D model is currently generated inside the template file so if you want to save it you should make a copy of the template before running the script.
In the sript_from_pydata.py file you can change some settings, currently only the dfmap file to use and the min and max coordinate values.