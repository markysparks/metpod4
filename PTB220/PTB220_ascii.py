import warnings
import logging
import re
import os
import serial
import value_checks
from datetime import datetime
from threading import Timer


class PTB220_ascii:
    def __init__(self):
        """Vaisala PTB220 sensor data extraction class. Extracts pressure,
        pressure change and trend from the sensor data output.
        """
        logging.basicConfig(level=logging.INFO)
        logging.captureWarnings(True)

        # .P.1  1012.05 ***.* * 1012.1 1012.0 1012.0 000.D5
        self.ptb220_pattern = re.compile('P....1\s\s\d+.\d+\s.+\.\d')
        self.pressure = None
        self.pressure_change = None
        self.pressure_trend = None
        self.timestamp = None

        self.serial_port_name = os.getenv('PTB220_PORT', '/dev/ttyUSB0')
        self.serial_baud = os.getenv('PTB220_BAUD', 9600)
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
        data falls within sensible boundaries. If necessary, the sensor must
        be setup to output its data in the required format.
        :param data_line: Sensor data output string.
        """
        """ Apply any instrument correction"""
        pressure_correction = float(os.getenv('PRESS_CORR', 0.0))

        # Only process output if we have PTB220 data
        if self.ptb220_pattern.search(data_line):
            data = find_numeric_data(data_line)

            if 5 < len(data) < 13:
                self.timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                if value_checks.pressure_check(float(data[2])):
                    self.pressure = float(data[2]) + pressure_correction
                    self.pressure_change = None
                    self.pressure_trend = None
                # Pressure change and trend only available after instrument
                # has been running for 3hrs
                if len(data) > 9:
                    if value_checks.tendency_check(float(data[3])):
                        self.pressure_change = float(data[3])
                    if value_checks.trend_check(int(data[4])):
                        self.pressure_trend = int(data[4])
        else:
            warnings.warn('PTB220 format not recognised', Warning)

    def get_readings(self):
        """
        Get the latest instrument readings.
        :return: JSON formatted instrument readings.
        """
        return [
            {
                'measurement': 'PTB220',
                'fields': {
                    'timestamp': self.timestamp,
                    'pressure': self.pressure,
                    'pressure_change': self.pressure_change,
                    'pressure_trend': self.pressure_trend
                }
            }
        ]


def find_numeric_data(data_line):
    """Use regular expressions to find and extract all digit data groups.
    This will include values like 1, 12.3, 2345, 0.34 i.e. any number or
    decimal number.
    :param data_line: The data line from digit groups are to be extracted.
    :return: A list containing the digit groups extracted.
    """
    data_search_exp = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ' \
                      ') )(?:' \
                      '[Ee] [+-]? \d+ ) ?'

    find_data_exp = re.compile(data_search_exp, re.VERBOSE)
    data = find_data_exp.findall(data_line)
    return data


if __name__ == '__main__':
    PTB220_ascii()
