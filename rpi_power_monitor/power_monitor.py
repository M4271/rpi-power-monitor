#!/usr/bin/python
import csv
import logging
import os
import pickle
import sys
import timeit
from datetime import datetime
from math import sqrt
from shutil import copyfile
from socket import AF_INET
from socket import SOCK_DGRAM
from socket import socket
from textwrap import dedent
from time import sleep

from prettytable import PrettyTable

import rpi_power_monitor.influx_interface as infl
from rpi_power_monitor.config import db_settings
from rpi_power_monitor.config import logger
from rpi_power_monitor.plotting import plot_data

from em112_reader import EM112Reader

class RPiPowerMonitor:
    """ Class to take readings from the EM112 and calculate power """
    def __init__(self):

        self.em112 = EM112Reader()
        self.em112.connect()

    def close_modbus(self):
        self.em112.close()

    def collect_data(self):
        """  Takes <num_samples> readings from the ADC for each ADC channel and returns a dictionary containing the CT channel number as the key, and a list of that channel's sample data.
        
        Arguments:
        num_samples -- int, the number of samples to collect for each channel.

        Returns a dictionary where the keys are ct1 - ct6, voltage, and time, and the value of each key is a list of that channel's samples (except for 'time', which is a UTC datetime)
        """
        now = datetime.utcnow()  # Get time of reading

        voltage_V = self.em112.read(0x00) / 10.0
        current_A = self.em112.read(0x02) / 1000.0
        power_W = self.em112.read(0x04) / 10.0
        energy_kwh = self.em112.read(0x10) / 10.0
        power_factor = self.em112.read(0x10C) / 1000.0

        samples = {
            'current_A': current_A,
            'power_W': power_W,
            'energy_kwh': energy_kwh,
            'voltage_V': voltage_V,
            'power_factor': power_factor,
            'time': now,
        }
        return samples

    def run_main(self):
        """ Starts the main power monitor loop. """
        logger.info("... Starting Raspberry Pi Power Monitor")
        logger.info("Press Ctrl-c to quit...")
        # The following empty dictionaries will hold the respective calculated values at the end
        # of each polling cycle, which are then averaged prior to storing the value to the DB.
        home_load_values = dict(power_W=[], energy_kwh=[], pf=[], current_A=[])
        net_power_values = dict(power_W=[], energy_kwh=[], pf=[], current_A=[])
        ct1_dict = dict(num=1, power_W=[], energy_kwh=[], pf=[], current_A=[], voltage_V=[])
        i = 0   # Counter for aggregate function

        while True:
            sleep(1)
            try:
                samples = self.collect_data()
                poll_time = samples['time']
                #print(samples)

                # Prepare values for database storage
                grid_1_power_W = samples['power_W']
                grid_1_energy_kwh = samples['energy_kwh']
                grid_1_current_A = samples['current_A']
                grid_1_voltage_V = samples['voltage_V']

                home_consumption_power_W = grid_1_power_W
                net_power_W = home_consumption_power_W
                home_consumption_current_A = grid_1_current_A
                net_current_A = grid_1_current_A

                # Average 2 readings before sending to db
                if i < 2:
                    home_load_values['power_W'].append(home_consumption_power_W)
                    home_load_values['current_A'].append(home_consumption_current_A)
                    net_power_values['power_W'].append(net_power_W)
                    net_power_values['current_A'].append(net_current_A)

                    ct1_dict['power_W'].append(samples['power_W'])
                    ct1_dict['current_A'].append(samples['current_A'])
                    ct1_dict['pf'].append(samples['power_factor'])
                    ct1_dict['energy_kwh'].append(samples['energy_kwh'])
                    ct1_dict['voltage_V'].append(samples['voltage_V'])
                    i += 1

                    # print(ct1_dict)
                else:
                    # Calculate the average, send the result to InfluxDB
                    # and reset the dictionaries for the next 2 sets of data.
                    # print("Writing to influx")
                    infl.write_to_influx(
                        home_load_values,
                        net_power_values,
                        ct1_dict,
                        poll_time,
                        i)
                    home_load_values = dict(power_W=[], energy_kwh=[], current_A=[])
                    net_power_values = dict(power_W=[], energy_kwh=[], current_A=[])
                    ct1_dict = dict(num=1, power_W=[], energy_kwh=[], pf=[], current_A=[], voltage_V=[])
                    i = 0

                    #if logger.handlers[0].level == 10:
                    #self.print_results(ct1_dict)

                # sleep(0.1)

            except KeyboardInterrupt:
                self.close_modbus() 
                infl.close_db()
                sys.exit()

    @staticmethod
    def print_results(results):
        t = PrettyTable(['', 'ct1'])
        t.add_row(['Power_W',
                   round(results['power_W'], 3)])
        t.add_row(['Current_A',
                   round(results['current_A'], 3)])
        t.add_row(['P.F.',
                   round(results['pf'], 3)])
        t.add_row(['Voltage_V',
                   round(results['voltage_V'], 3)])
        s = t.get_string()
        logger.debug(f"\n{s}")

    @staticmethod
    def get_ip():
        """ Determines your Pi's local IP address so that it can be displayed to the user for ease of accessing generated plots. 
        
        Returns a string representing the Pi's local IP address that's associated with the default route.
        """
        
        s = socket(AF_INET, SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except:
            ip = None
        finally:
            s.close()
        return ip


if __name__ == '__main__':
    try:  # Backup config.py file
        copyfile('config.py', 'config.py.backup')
    except FileNotFoundError:
        logger.info("Could not create a backup of config.py file.")

    rpm = RPiPowerMonitor()

    # Try to establish a connection to the DB for 5 seconds:
    x = 0
    connection_established = False
    logger.info(f"... Trying to connect to database at: {db_settings['host']}:{db_settings['port']}")
    while x < 5:
        connection_established = infl.init_db()
        if connection_established:
            break
        else:
            sleep(1)
            x += 1

    if not connection_established:
        if (db_settings['host'] == 'localhost' or
                '127.0' in db_settings['host'] or
                rpm.get_ip() in db_settings['host']):
            logger.critical(f"Could not connect to InfluxDB on this Pi. Please check the status of Influx with 'sudo systemctl status influxdb'.")
            sys.exit()
        else:
            logger.info(
                f"Could not connect to your remote database at {db_settings['host']}:{db_settings['port']}. "
                f"Please verify connectivity/credentials and try again.")
            sys.exit()
    else:
        rpm.run_main()

