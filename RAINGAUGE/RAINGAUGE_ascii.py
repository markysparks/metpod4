import warnings
import logging
import re
import os
import requests
import serial
import value_checks
from datetime import datetime
from threading import Timer


class RAINGAUGE_ascii:
    def __init__(self):
        """Digital rain gauge data extraction class. This a tipping bucket
        rain gauge that outputs a data message over a serial port containing
        rain rate, tip and units information.
        """
        logging.basicConfig(level=logging.INFO)
        logging.captureWarnings(True)

        # {"rainrate”: 0.0, "raintip”: 0.0, "units": "mm/hr"}
        self.rain_gauge_pattern = re.compile('"rainrate": .+, "raintip": .+,')

        self.rainrate = 0.0
        self.raintip = 0.0
        self.timestamp = None

        self.serial_port_name = os.getenv('RAINGAUGE_PORT', '/dev/ttyUSB0')
        self.serial_baud = os.getenv('RAINGAUGE_BAUD', 9600)
        self.serial_port = serial.Serial(self.serial_port_name, self.serial_baud, timeout=1.0)
        logging.info('Serial port: ' + str(self.serial_port))
        logging.info('Sensor mode: ascii')

        self.serial_port_reader()

    def serial_port_reader(self):
        """Read a line of incoming data from the assigned serial port, then
        pass the data onto a processor for extraction of the data values"""
        try:
            data_bytes = self.serial_port.readline()
            data_line = str(data_bytes)
            # Only process output if we have actual data in the line
            if len(data_line) > 3:
                logging.info('RAW data: ' + data_line)
                self.data_decoder(data_line)
                logging.info(self.get_readings())
        except serial.SerialException as error:
            warnings.warn("Serial port error: " + str(error), Warning)
        # Asynchronously schedule this function to be run every 1 seconds
        Timer(1, self.serial_port_reader).start()

    def data_decoder(self, data_line):
        """
        Extract available weather parameters from the sensor data, check that
        data is the correct format and falls within sensible boundaries.
        If necessary, the sensor must be setup to output its data in the required format.
        :param data_line: Sensor data output string.
        """
        if self.rain_gauge_pattern.search(data_line):
            data = find_numeric_data(data_line)
            if 1 < len(data) < 3:
                self.timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                self.rainrate = float(data[0])
                self.raintip = float(data[1])

            """ Check parameters fall within sensible limits """
            if value_checks.rain_rate_check(self.rainrate):
                requests.post('http://rainfall', data=str(self.raintip), timeout=5)
            else:
                warnings.warn('invalid Raingauge data!', Warning)

    def get_readings(self):
        return [
            {
                'measurement': 'raingauge',
                'fields': {
                    'timestamp': self.timestamp,
                    'rainrate': self.rainrate,
                    'raintip': self.raintip
                }
            }
        ]


def find_numeric_data(dataline):
    """Use regular expressions to find and extract all digit data groups.
    This will include values like 1, 12.3, 2345, 0.34 i.e. any number or
    decimal number.
    :param dataline: The data line from digit groups are to be extracted.
    :return: A list containing the digit groups extracted.
    """
    data_search_exp = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ' \
                      ') )(?:' \
                      '[Ee] [+-]? \d+ ) ?'

    find_data_exp = re.compile(data_search_exp, re.VERBOSE)
    data = find_data_exp.findall(dataline)
    return data
