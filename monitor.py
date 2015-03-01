#!/usr/bin/env python

'''
# http://sharedmemorydump.net/post/2013-07-18-logging-data-temperature-with-raspberry-pi
# https://github.com/Pyplate/rpi_temp_logger/blob/master/monitor.py
# http://sebastianraschka.com/Articles/2014_sqlite_in_python_tutorial.html
# http://bradsrpi.blogspot.nl/2014/06/c-program-to-read-multiple-ds18b20-1.html
# https://help.github.com/articles/generating-ssh-keys/#platform-linux
'''

'''
sqlite> .schema sensor_data
CREATE TABLE sensor_data( id           integer primary key autoincrement not null
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

# global variables
speriod=(15*60)-1
dbname='/var/www/temp.sqlite'

# store the temperature in the database
def log_temperature(id, temp):
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()

	query = "INSERT INTO sensor_data (sensor_id,value) VALUES ('"+str(id)+"','"+str(temp)+"');"
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
			print "Device ID ("+deviceid+") ; Temperature ("+str(temperature)+")"

			# Store the temperature in the database
			log_temperature(deviceid, temperature)

if __name__=="__main__":
	# go and find all the wire_one devices  and store the ID and temperature in the SQLite database
	main()
