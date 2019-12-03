from Sensor_Manager import Main
import application
import threading
import concurrent.futures
from application import app

def pythonThread():
    Main()



if __name__ == "__main__":
    import os
    import sys
    import psutil 
    import logging
    print(psutil.Process(os.getpid()))

    x = threading.Thread(target=pythonThread)
    x.start()

    app.run(host='0.0.0.0')

