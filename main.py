import configparser
import logging
import sys
import threading
import time
import traceback
import os

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMessageBox

from data_processor import DataProcessor
from data_reader import DataReader
from ui import MainWindow


def logger_init():
    logconfig = {
        'version': 1,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': 'DEBUG'
            },
            'data_reader': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'level': 'DEBUG',
                'maxBytes': 10 * 1024,
                'backupCount': 3,
                'filename': 'logs/data_reader.log',
                'mode': 'a'

            },
            'main_win': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'level': 'DEBUG',
                'maxBytes': 10 * 1024,
                'backupCount': 3,
                'filename': 'logs/main.log',
                'mode': 'a'

            }
        },
        'formatters': {
            'default': {
                'format': '%(asctime)s %(levelname)-8s %(name)-12s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'loggers': {
            'main_win': {
                'handlers': ['console', 'main_win'],
                'level': 'DEBUG'
            },
            'data_reader': {
                'handlers': ['console', 'data_reader'],
                'level': 'DEBUG'
            }
        }
    }
    if not os.path.exists('logs'):
        os.mkdir('logs')
    logging.config.dictConfig(logconfig)


class DataManager(QObject):
    data_changed = pyqtSignal(list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = configparser.ConfigParser()
        config.read('config.ini')
        addresses = [config.get('DataReader', f'bt_{i}') or None for i in range(1, 10)]
        self.data_readers = [DataReader(i, address=addr) for i, addr in zip(range(9), addresses)]
        self.data_processor = DataProcessor(9)
        self.period = float(config.get('DataReader', f'period'))

    def start(self):
        threading.Thread(target=self.loop).start()

    def loop(self):
        while True:
            t0 = time.time()
            self.update()
            sleep_timeout = self.period - (time.time() - t0)
            if sleep_timeout > 0:
                time.sleep(sleep_timeout)

    def update(self):
        dfs = []
        for i, data_reader in enumerate(self.data_readers):
            try:
                data = data_reader.read()
            except Exception as ex:
                data = None
            if data:
                self.data_processor.add_data(i, data)
            df = self.data_processor.get_data(i)
            dfs.append(df)
        self.data_changed.emit(dfs)


def main():
    logger_init()
    check_config()
    app = QApplication([])
    data_manager = DataManager()
    data_manager.start()

    main_win = MainWindow(data_manager)
    main_win.init()

    data_manager.data_changed.connect(main_win.change_plots)
    main_win.show()
    try:
        sys.exit(app.exec_())
    except Exception:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(traceback.format_exc())
        msg.exec_()


def check_config():
    config = configparser.ConfigParser()
    if not config.read('config.ini'):
        config['Report'] = {
            'max_voltage': '15.5',
            'min_voltage': '11.9',
            'max_voltage_diff': '0.35',
            'max_temperature': '42.5',
            'min_temperature': '5.0'
        }
        config['DataReader'] = {
            **{f'bt_{i}': '' for i in range(1, 10)},
            'period': '60.0'}
        with open('config.ini', 'w') as f:
            config.write(f)
    return config.read('config.ini')


if __name__ == '__main__':
    main()
