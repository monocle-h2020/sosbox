import Sensor_Manager
import os
import sys
import psutil
import logging
import signal
import time

def AddRestart(newSensor, port, uniqueName):
    pid = Sensor_Manager.AddSensor(newSensor, port, uniqueName)
    if(pid == "Not happy"):
        print("Port was not good") 
    else:
        os.kill(pid.pid, signal.SIGKILL)