from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBServerError
from requests.exceptions import ConnectionError

from rpi_power_monitor.config import db_settings
from rpi_power_monitor.config import logger

# Changes to these settings should be made in config.py!
client = InfluxDBClient(
    host=db_settings['host'],
    port=db_settings['port'],
    username=db_settings['username'],
    password=db_settings['password'],
    database=db_settings['database'])


class Point:
    def __init__(self, p_type, *args, **kwargs):
        if p_type == 'home_load':
            self.power_W = kwargs['power_W']
            self.current_A = kwargs['current_A']
            self.energy_kwh = kwargs['energy_kwh']
            self.p_type = p_type
            self.time = kwargs['time']
        
        elif p_type == 'net': 
            '''
            This type represents the current net power situation at the time of sampling. 
            self.power   : the real net power
            self.current : the rms current as measured
            self.p_type  : the type of point [home_load, solar, net, ct, voltage]
            self.time    : timestamp from when the data was sampled
            '''
            self.power_W = kwargs['power_W']
            self.current_A = kwargs['current_A']
            self.energy_kwh = kwargs['energy_kwh']
            self.p_type = p_type
            self.time = kwargs['time']
        
        elif p_type == 'ct':
            '''
            This type represents a CT reading.
            self.power   : the real power as calculated in the calculate_power() function
            self.current : the rms current as measured
            self.p_type  : the type of point [home_load, solar, net, ct, voltage]
            self.ct_num  : the CT number [0-6]
            self.time    : timestamp from when the data was sampled
            '''
            self.power_W = kwargs['power_W']
            self.current_A = kwargs['current_A']
            self.voltage_V = kwargs['voltage_V']
            self.energy_kwh = kwargs['energy_kwh']
            self.p_type = p_type
            self.pf = kwargs['pf']
            self.time = kwargs['time']
            self.ct_num = kwargs['num']

    def to_dict(self):
        if self.p_type == 'home_load':
            data = {
                "measurement": self.p_type,
                "fields": {
                    "current_A": self.current_A,
                    "power_W": self.power_W,
                    "energy_kwh": self.energy_kwh,
                },
                "time": self.time
            }
        elif self.p_type == 'net':
            data = {
                "measurement": self.p_type,
                "fields": {
                    "current_A": self.current_A,
                    "power_W": self.power_W,
                    "energy_kwh": self.energy_kwh,
                },
                "time": self.time
            }

        elif self.p_type == 'ct':
            data = {
                "measurement": self.p_type,
                "fields": {
                    "current_A": self.current_A,
                    "power_W": self.power_W,
                    "energy_kwh": self.energy_kwh,
                    "pf": self.pf,
                    "voltage_V": self.voltage_V,
                },
                "tags": {
                    "ct": self.ct_num
                },
                "time": self.time
            }

        else:
            return

        return data


def init_db():
    try:
        client.create_database(db_settings['database'])
        logger.info("... DB initialized.")
        return True
    except ConnectionRefusedError:
        logger.debug("Could not connect to InfluxDB")
        return False
    except Exception:
        logger.debug(f"Could not connect to {db_settings['host']}:{db_settings['port']}")
        return False


def close_db():
    client.close()


def write_to_influx(home_load_values,
                    net_power_values,
                    ct1_dict,
                    poll_time,
                    length):

    # Create Points
    home_load = Point('home_load',
                      power_W    = sum(home_load_values['power_W']) / length,
                      energy_kwh = sum(home_load_values['energy_kwh']) / length,
                      current_A  = sum(home_load_values['current_A']) / length,
                      time=poll_time)
    net =       Point('net',      
                      power_W    = sum(net_power_values['power_W']) / length,
                      energy_kwh = sum(net_power_values['energy_kwh']) / length,
                      current_A  = sum(net_power_values['current_A']) / length,
                      time=poll_time)
    ct1 =       Point('ct',   
                      power_W    = sum(ct1_dict['power_W']) / length,
                      energy_kwh = sum(ct1_dict['energy_kwh']) / length,
                      current_A  = sum(ct1_dict['current_A']) / length,
                      pf         = sum(ct1_dict['pf']) / length,
                      voltage_V  = sum(ct1_dict['voltage_V']) / length,
                      num        = ct1_dict['num'],
                      time=poll_time)

    points = [
        home_load.to_dict(),
        net.to_dict(),
        ct1.to_dict(),
    ]

    #print(points)

    try:    
        client.write_points(points, time_precision='ms')
    except InfluxDBServerError as e:
        logger.critical(f"Failed to write data to Influx. Reason: {e}")
    except ConnectionError:
        logger.info("Connection to InfluxDB lost. Please investigate!")
        quit()


if __name__ == '__main__':
    client = InfluxDBClient(host='localhost', port=8086, username='root', password='password', database='example')
    # test_insert_and_retrieve(client)
