import warnings
import logging
import re
import os
import serial
import value_checks
from datetime import datetime
from threading import Timer
from wind_processor import WindProcessor


class WINDSONIC_ascii:
    def __init__(self):
        """Gill Windsonic data collection and extraction class. Read an ascii
        data line from the sensor and extract values of wind speed and
        direction.
        """
        logging.basicConfig(level=logging.DEBUG)
        logging.captureWarnings(True)

        # b'\x02Q,194,000.04,N,00,\x0315\r\n'
        self.windsonic_pattern = re.compile('\w,\d\d\d,\d\d\d.\d\d,\w,\d\d')

        self.serial_port_name = os.getenv('WINDSONIC_PORT', '/dev/ttyUSB0')
        self.serial_baud = os.getenv('WINDSONIC_BAUD', 9600)
        self.serial_port = serial.Serial(self.serial_port_name, self.serial_baud, timeout=1.0)
        logging.info('Serial port: ' + str(self.serial_port))
        logging.info('Sensor mode: ascii')

        self.timestamp = None
        self.winddir = None
        self.windspeed = None
        self.winddir_avg10m = None
        self.winddir_avg2m = None
        self.windspeed_avg10m = None
        self.windspeed_avg2m = None
        self.windgust = None
        self.wind_processor = WindProcessor()

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
        # Asynchronously schedule this function to be run again in 1.0 seconds
        Timer(1, self.serial_port_reader).start()

    def data_decoder(self, data_line):
        """
        Extract available weather parameters from the sensor data, check that
        data falls within sensible boundaries. If necessary, the sensor must
        be setup to output its data in the required format e.g.
        '\x02Q,194,005.04,N,00,\x0315' with units in knots and degrees
        (194 degrees and 5.04 kts in this case).
        :param data_line: Sensor data output string.
        """
        """ Apply any instrument correction"""
        anemo_offset = int(os.getenv('ANEMO_OFFSET', 0))

        # Only process output if we have Gill Windsonic data
        if self.windsonic_pattern.search(data_line):
            data = find_numeric_data(data_line)

            if data is not None and 3 < len(data) < 6:
                self.timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                winddir_raw = int(round(float(data[1]), 0)) + anemo_offset
                if winddir_raw == 0:
                    pass
                elif winddir_raw < 0:
                    winddir_raw += 360
                elif winddir_raw > 360:
                    winddir_raw -= 360
                windspeed_raw = int(round(float(data[2]), 0))
                if value_checks.windspeed_check(windspeed_raw) \
                        and value_checks.winddir_check(winddir_raw):
                    self.winddir = winddir_raw
                    self.windspeed = windspeed_raw
                    self.process_wind_data()
            else:
                warnings.warn('Invalid WindSonic data!', Warning)

    def process_wind_data(self):
        """Uses the current instantaneous wind speed and direction as inputs
        to a wind_processor object that deals with calculating mean
        wind speeds, directions and max gust for 10 and 2 minute periods.
        :return: Current 10 minute and 2 minute mean wind speeds, directions
        and maximum gust for each period.
        """
        mean10min = self.wind_processor.process_wind_10min(self.winddir,
                                                           self.windspeed)
        mean2min = self.wind_processor.process_wind_2min(self.winddir,
                                                         self.windspeed)
        if self.wind_processor.flag10min:
            self.winddir_avg10m = mean10min[0]
            self.windspeed_avg10m = mean10min[1]
            self.windgust = mean10min[2]
            self.winddir_avg2m = mean2min[0]
            self.windspeed_avg2m = mean2min[1]

    def get_readings(self):
        """
        Get the latest instrument readings.
        :return: JSON formatted instrument readings.
        """
        return [
            {
                'measurement': 'WINDSONIC',
                'fields': {
                    'timestamp': self.timestamp,
                    'winddir': self.winddir,
                    'windspeed': self.windspeed,
                    'windgust': self.windgust,
                    'winddir_avg10m': self.winddir_avg10m,
                    'windspeed_avg10m': self.windspeed_avg10m,
                    'winddir_avg2m': self.winddir_avg2m,
                    'windspeed_avg2m': self.windspeed_avg2m,
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
    WINDSONIC_ascii()
