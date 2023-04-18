import logging
import sys

# Create basic logger
logger = logging.getLogger('power_monitor')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)
logger.addHandler(ch)

# InfluxDB Settings
db_settings = {
    'host': 'localhost',
    'port': 8086,
    'username': 'root',
    'password': 'password',
    'database': 'power_monitor'
}

