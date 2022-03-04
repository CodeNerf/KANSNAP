# About canSNARE

ccanSNARE is the datalogger web application intended for
use on a Raspberry Pi 4.  It has been tested with up to 5 active can interfaces and 3 simultaneous video streams. Including remote screencapture with the assistance of OBS and the remote RTSP plugin. 

All captures are stored in the `static/captures` directory with the folder hierarchy being <Vehicle_VIN>\<Captured_Parameter_ID>\<data>

## Starting canSNARE

Simply execute the following from within the root of the canSNARE
directory.

    $ python3 run.py

## Updating canSNARE

Updating canSNARE, currently, is as simple as pulling the git repository
and restarting run.py

## Instructions for New Features

Leveraging OBS and the RTSP server plugin, you can broadcast a local screen capture to the pi.

For OBS instructions, consult their documentation. 

To initialize OBS for screen capture, once your scene is set, to `Tools -> RTSP Server`. Make sure that the port is set to `4747` and the ending url is `/video` **EX: The target for OBS Should look like `rtsp://localhost:4747/video`**. Then click Start.

In the capture screen, you must enter the ip address of the computer that's running OBS. If you're on a hotspot or local network this will most likely will have a `192.168.*.*` address or if you're on the vpn a `10.*.*.*` address. Once the IP is set, click `Enable Screen Capture`. 

## Feature Requests and Bugs
Please use the issues tab for any feature requests or bus. Please label them with either [Bug] or [Feature Request]. 
