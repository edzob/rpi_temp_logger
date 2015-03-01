#!/usr/bin/env python
# -*- coding: utf-8 -*- 

'''
# examples on how to put DS18B20 data into a log file/database
## http://sharedmemorydump.net/post/2013-07-18-logging-data-temperature-with-raspberry-pi
## https://github.com/Pyplate/rpi_temp_logger/blob/master/monitor.py
## http://sebastianraschka.com/Articles/2014_sqlite_in_python_tutorial.html
## http://bradsrpi.blogspot.nl/2014/06/c-program-to-read-multiple-ds18b20-1.html
# Examples on how to put DHT11 data into a log file/database
## https://github.com/DzikuVx/raspberry_temperature_log/blob/master/get_data.py
## https://github.com/Hexalyse/RPi-weather-log/blob/master/log_weather.py
## https://chrisbaume.wordpress.com/category/technology/raspberry-pi/ 
#### This library is really nice to add DHT11 data. Do know that you need to look at my commend on the blog on the non BCG-GPIO pin 4 configurations.
### when using the Chris Baume library, please do add the dht11 binary to the sudo file via .. sudo visudo .. see:
### http://askubuntu.com/questions/155791/how-do-i-sudo-a-command-in-a-script-without-being-asked-for-a-password
'''
'''
sqlite> .schema sensor_temperature_data
CREATE TABLE sensor_temperature_data( id           integer primary key autoincrement not null
                        , timestamp    datetime default current_timestamp not null
                        , sensor_id    integer not null
                        , value        real not null);

sqlite> .schema sensor_humidity_data
CREATE TABLE sensor_humidity_data( id           integer primary key autoincrement not null
                        , timestamp    datetime default current_timestamp not null
                        , sensor_id    integer not null
                        , value        real not null);

sqlite> .schema sensors
CREATE TABLE sensors( sensor_id        integer primary key
                    , sensor_type      text not null
                    , sensor_name      text not null
                    , sensor_location  text not null );
'''

import sqlite3
import os
import glob
import commands

# global variables
speriod=(15*60)-1
dbname='/var/www/temp.sqlite'

# store the temperature in the database
def log_temperature(id, temp):
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()

	query = "INSERT INTO sensor_temperature_data (sensor_id,value) VALUES ('"+str(id)+"','"+str(temp)+"');"
	print query
	curs.execute(query)

	# commit the changes
	conn.commit()
	conn.close()

# store the humidity in the database
def log_humidity(id, hum):
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()

	query = "INSERT INTO sensor_humidity_data (sensor_id,value) VALUES ('"+str(id)+"','"+str(hum)+"');"
	print query
	curs.execute(query)

	# commit the changes
	conn.commit()
	conn.close()

# display the contents of the database
def display_data(id):
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()

	for row in curs.execute("SELECT * FROM sensor_data WHERE sensor_id =?", id):
		print str(row[0])+"	"+str(row[1])

	conn.close()

# get temperature
# returns None on error, or the temperature as a float
def get_temp(devicefile):
	try:
		fileobj = open(devicefile,'r')
		lines = fileobj.readlines()
		fileobj.close()
	except:
		return None

	# get the status from the end of line 1 
	status = lines[0][-4:-1]

	# is the status is ok, get the temperature from line 2
	if status=="YES":
		tempstr= lines[1][-6:-1]
		tempvalue=float(tempstr)/1000
		return tempvalue
	else:
		print "There was an error."
		return None

# main function
# This is where the program starts 
def main():
	# enable kernel modules
	os.system('sudo modprobe w1-gpio')
	os.system('sudo modprobe w1-therm')

	# search for a device file that starts with 28
	base_dir = '/sys/bus/w1/devices/'
	devicelist = glob.glob(base_dir + '28*')

	if devicelist=='':
		# apparently no devices found
		return None
	else:
		# append /w1slave to the devices because the temperatures are in that sub directory.
		for w1devicefile in devicelist:
			w1devicefile  = w1devicefile + '/w1_slave'

			# get the temperature from the device file
			temperature = get_temp(w1devicefile)

			# Sometimes reads fail on the first attempt, so we need to retry until we succeed
			while temperature == None:
				temperature = get_temp(w1devicefile)

			deviceid = w1devicefile.split("/")[5]
			# print "Device ID ("+deviceid+") ; Temperature ("+str(temperature)+")"

			# Store the temperature in the database
			log_temperature(deviceid, temperature)

	output = (commands.getstatusoutput('sudo /home/pi/code/wiringPi/examples/dht11'))[1].split(",")
	log_temperature("DHT11-1", output[1])
	log_humidity("DHT11-1", output[0])

if __name__=="__main__":
	# go and find all the wire_one devices  and store the ID and temperature in the SQLite database
	main()
