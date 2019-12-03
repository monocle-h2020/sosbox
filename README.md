# SOS-box

The SOS-box is a software based data logger ready to accept a range of sensors, 
parsing and processesing the data stream from the sensors to be stored in a
local database, which is then ready for SOS to extract and share with SOS capable servers. 

## Description
When the program is run it will ask the user what sensors are connected, 
then create an object of each of those sensors, move them into their own threads 
so reading data can be done concurrently and so their timers don't interfere.
After reading a line of data, it is formatted and then sent to the apropriate 
table in the database.

The layout is as follows:  
- sensor_manager is the main programe which the user 
interacts with and creates the sensor objects, holds the threads which talk to 
the sensor reader programs, and communicates with the SQL query functions. 
- sensor_factory creates the sensor object using the factory design pattern.
- SQL_queries is where all insert statements are contained in their own
functions which are called by the appropriate sensor object.
- Config.ini contains the database access data as well as the sensors entered 
by the user.
- dummy_sensors is used to simulate sensor output, since we don't have access 
to all the actual sensors we are programming for.
- All other files are readers for specific sensors, which actually read and 
format the data from the sensor.

## Support

Contact by email monocle@pml.ac.uk

## Authors and acknowledgement

Jaime Kershaw Brown - main contributor - Plymouth Marine Laboratory
Darren Snee - secondary contributor & advisor - Plymouth Marine Laboratory

## License

To be updated.

## Project status

In progress
