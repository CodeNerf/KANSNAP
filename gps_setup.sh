#!/bin/bash

sleep 0.5
sudo minicom -b 115200 -D /dev/ttyUSB3 -S /etc/minicom_setup.txt
sleep 0.5
sudo minicom -b 115200 -D /dev/ttyUSB1
sleep 0.5
sudo systemctl stop gpsd.socket
sleep 0.5
sudo systemctl disable gpsd.socket
sleep 0.5
sudo gpsd /dev/ttyUSB1