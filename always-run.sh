#!/bin/bash
sleep 10
cd /home/pi/Documents/sensor_recorder
while true; do
    /usr/bin/python3 ProgramController.py
done 
