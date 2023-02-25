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
# from data_reader import DataReader
from data_reader import SimDataReader as DataReader
from ui import MainWindow
from plot import Plot, BigPlot, PlotProperties


class DataManager(QObject):
    data_changed = pyqtSignal(list)

    def __init__(self, number=9, *args, **kwargs):
        self.logger = logging.getLogger(f'manager')
        super().__init__(*args, **kwargs)
        config = configparser.ConfigParser()
        config.read('config.ini')
        addresses = [config.get('DataReader', f'bt_{i + 1}') or None for i in range(number)]
        self.data_readers = [DataReader(i, address=addr) for i, addr in zip(range(number), addresses)]
        self.data_processor = DataProcessor(number)
        self.plots = [Plot() for _ in range(number)]
        self.big_plot = BigPlot()
        self.plot_properties = PlotProperties()
        self.big_plot_number = None
        self.period = float(config.get('DataReader', f'period'))
        self.__run = True

    def start(self):
        threading.Thread(target=self.loop).start()

    def stop(self):
        self.__run = False

    def loop(self):
        while self.__run:
            t0 = time.time()
            self.update()
            sleep_timeout = self.period - (time.time() - t0)
            if sleep_timeout > 0:
                time.sleep(sleep_timeout)

    def update(self):
        self.data_processor.begin_circle()
        t0 = time.time()
        self.logger.debug('start read')
        for i, data_reader in enumerate(self.data_readers):
            try:
                data = data_reader.read()
            except Exception as ex:
                data = None
            if data:
                self.data_processor.add_data(i, data)
        self.logger.debug(f'end read {round(time.time() - t0, 3)} sec')
        self.data_processor.end_circle()

        t0 = time.time()
        self.logger.debug('update plots')
        for i, df, plot in zip(range(len(self.data_processor.dfs)), self.data_processor.dfs, self.plots):
            if df is not None and not df.empty:
                plot.create_plot(df, f'{i + 1}', self.plot_properties)
        self.logger.debug(f'end update plots {round(time.time() - t0, 3)} sec')
        if self.big_plot_number is not None:
            self.update_big_plot(self.big_plot_number)

        self.data_changed.emit(self.data_processor.dfs)

    def update_big_plot(self, number):
        self.big_plot_number = number
        if self.big_plot_number is not None:
            self.big_plot.create_plot(
                self.data_processor.dfs[self.big_plot_number], str(self.big_plot_number + 1), self.plot_properties)


def main():
    logger_init()
    check_config()
    app = QApplication([])
    data_manager = DataManager()
    data_manager.start()

    main_win = MainWindow(data_manager)
    main_win.init(data_manager.plots, data_manager.big_plot, data_manager.plot_properties)

    data_manager.data_changed.connect(main_win.change_plots)
    data_manager.data_changed.connect(main_win.draw_big_plot)
    main_win.create_big_plot.connect(data_manager.update_big_plot)
    main_win.show()
    try:
        res = app.exec_()
        data_manager.stop()
        sys.exit(res)
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
        config['Plot'] = {}
        config['DataReader'] = {
            **{f'bt_{i}': '' for i in range(1, 10)},
            'period': '60.0'}
        with open('config.ini', 'w') as f:
            config.write(f)
    return config.read('config.ini')


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
            'data_manager': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'level': 'DEBUG',
                'maxBytes': 10 * 1024,
                'backupCount': 3,
                'filename': 'logs/data_manager.log',
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
            },
            'manager': {
                'handlers': ['console', 'data_manager'],
                'level': 'DEBUG'
            }
        }
    }
    if not os.path.exists('logs'):
        os.mkdir('logs')
    logging.config.dictConfig(logconfig)


if __name__ == '__main__':
    main()
