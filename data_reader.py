import logging
from datetime import datetime
from time import sleep
import socket
import random


class DataReader:

    def __init__(self, number, address):
        self.number = number
        self.address = address
        self.serial = None
        self.logger = logging.getLogger(f'data_reader.{self.number}')

    def read(self):
        if not self.address:
            return
        with socket.socket(socket.AF_BLUETOOTH,
                           socket.SOCK_STREAM,
                           socket.BTPROTO_RFCOMM) as c:
            self.logger.debug('socket opened')
            c.connect((self.address, 1))
            self.logger.debug('socket connected')
            c.send(b'get_data')
            self.logger.debug('data sent')
            sleep(3.0)
            data = c.recv(1024).decode()
            data_for_log = data.replace('\n', '\\n').replace('\r', '\\r')
            self.logger.debug(f'data received: {data_for_log}')
            if data.startswith('<get_data'):
                lines = data.split('\n')
                t, v, c = [float(l.split(':')[1]) for l in lines[1].split(';')]
                return {
                    'dtime': datetime.now(),
                    'current': c,
                    'voltage': v,
                    'temperature': t,
                }
            else:
                self.logger.error(f'bad data: {data}')


class SimDataReader:

    def __init__(self, number):
        self.number = number

    def read(self):
        return {
            'dtime': datetime.now(),
            'current': random.random() + 10.0,
            'voltage': random.random() + 12.0,
            'temperature': random.random() * 3 + 18.0,
        }
