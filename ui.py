import time

from PyQt5.QtCore import Qt, QAbstractTableModel, QDateTime, QDate, QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import *
import logging
import logging.config

import matplotlib

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class MainWindow(QMainWindow):

    create_big_plot = pyqtSignal(int)

    def __init__(self, data_manager, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.spin_em2_shift = None
        self.chk_show_extra_pen = None
        self.chk_show_legend = None
        self.chk_show_corrected = None
        self.table_win = None
        self.date = ''
        self.em2_shift = 0
        self.object_data = None
        self.kit_win = None
        self.plot_params = {}
        self.plot_canvas = []
        self.plot_properties = None
        self.big_plot = BigPlotWindow()
        self.logger = logging.getLogger('main_win')

    def init(self, plots, big_plot, plot_properties):
        for i, plot in enumerate(plots):
            canvas = MplCanvas(i, self, width=5, height=4, dpi=100)
            canvas.set_plot(plot)
            canvas.mpl_connect("button_press_event", self.on_canvas_click)
            self.plot_canvas.append(canvas)
        self.big_plot.set_plot(big_plot)
        self.plot_properties = plot_properties
        self.init_ui()
        self.build_plot_data(self.plot_canvas)

    def init_ui(self):
        self.setWindowTitle("Monitor")
        toolbar = QToolBar("My main toolbar", parent=self)
        self.addToolBar(toolbar)

        central_widget = QWidget()

        button_action = QAction("Table", self)
        button_action.setStatusTip("Table")
        button_action.triggered.connect(self.open_table)
        toolbar.addAction(button_action)

        box = QVBoxLayout()
        grid_layout = QGridLayout()
        for i, plot in enumerate(self.plot_canvas):
            grid_layout.addWidget(plot, i // 3, i % 3)
        box.addLayout(grid_layout)
        control_layout = QHBoxLayout()

        btn_plot_time_left = QPushButton('<')
        btn_plot_time_left.clicked.connect(self.plot_time_left)
        btn_plot_time_right = QPushButton('>')
        btn_plot_time_right.clicked.connect(self.plot_time_right)
        btn_plot_time_plus = QPushButton('+')
        btn_plot_time_plus.clicked.connect(self.plot_time_plus)
        btn_plot_time_minus = QPushButton('-')
        btn_plot_time_minus.clicked.connect(self.plot_time_minus)
        lbl_em2_shift = QLabel(text='ЭМ2 shift:')
        self.spin_em2_shift = QSpinBox()
        self.spin_em2_shift.setMinimum(-3600 * 24)
        self.spin_em2_shift.setMaximum(3600 * 24)
        # self.spin_em2_shift.setSingleStep(10)
        # self.spin_em2_shift.editingFinished.connect(self.update_plot)
        self.spin_em2_shift.textChanged.connect(self.update_plot)
        self.chk_show_extra_pen = QCheckBox('Extra pens')
        self.chk_show_extra_pen.stateChanged.connect(self.update_plot)
        self.chk_show_legend = QCheckBox('Legend')
        self.chk_show_legend.stateChanged.connect(self.update_plot)
        self.chk_show_corrected = QCheckBox('Corrected')
        self.chk_show_corrected.setChecked(True)
        self.chk_show_corrected.stateChanged.connect(self.update_plot)
        control_layout.addWidget(btn_plot_time_left)
        control_layout.addWidget(btn_plot_time_plus)
        control_layout.addWidget(btn_plot_time_minus)
        control_layout.addWidget(btn_plot_time_right)
        control_layout.addWidget(lbl_em2_shift)
        control_layout.addWidget(self.spin_em2_shift)
        control_layout.addWidget(self.chk_show_extra_pen)
        control_layout.addWidget(self.chk_show_legend)
        control_layout.addWidget(self.chk_show_corrected)

        # box.addLayout(control_layout)
        central_widget.setLayout(box)
        self.setCentralWidget(central_widget)
        # self.resize(800, 600)
        self.showMaximized()

    def change_plots(self):
        t0 = time.time()
        self.logger.debug('change_plots')
        for canvas in self.plot_canvas:
            canvas.draw()
        self.logger.debug(f'end change_plots {round(time.time() - t0, 3)} sec')

    def draw_big_plot(self):
        if self.big_plot.isVisible():
            self.big_plot.canvas.draw()

    def on_canvas_click(self, evt):
        self.logger.info(f'on_canvas_click #{evt.canvas.number}')
        self.big_plot.number = evt.canvas.number
        self.create_big_plot.emit(evt.canvas.number)
        if self.big_plot.isVisible():
            self.big_plot.setFocus()
            self.big_plot.activateWindow()
        else:
            self.big_plot.showMaximized()

    def prepare_dataframes(self):
        pass

    def build_plot_data(self, canvas):
        self.plot_properties.show_extra_pen = self.chk_show_extra_pen.isChecked()
        self.plot_properties.show_corrected = self.chk_show_corrected.isChecked()
        self.plot_properties.show_legend = self.chk_show_legend.isChecked()
        # self.plot_properties.x_min = self.plot_params.get('x_min')
        # self.plot_properties.x_max = self.plot_params.get('x_max')
        # self.plot_properties.em2_shift = self.spin_em2_shift.value() * 1000
        # self.change_plots([None] * len(self.plot_canvas))

    def open_table(self):
        pass

    def plot_time_left(self):
        d = self.plot_params['x_max'] - self.plot_params['x_min']
        # self.plot_params['x_min'] = max(0, self.plot_params['x_min'] - d / 2)
        # self.plot_params['x_max'] = max(d, self.plot_params['x_max'] - d / 2)
        self.plot_params['x_min'] = self.plot_params['x_min'] - d / 2
        self.plot_params['x_max'] = self.plot_params['x_max'] - d / 2
        self.build_plot_data(self.plot_canvas)

    def plot_time_right(self):
        d = self.plot_params['x_max'] - self.plot_params['x_min']
        self.plot_params['x_min'] += d / 2
        self.plot_params['x_max'] += d / 2
        self.build_plot_data(self.plot_canvas)

    def plot_time_plus(self):
        d = self.plot_params['x_max'] - self.plot_params['x_min']
        self.plot_params['x_max'] -= d / 2
        self.build_plot_data(self.plot_canvas)

    def plot_time_minus(self):
        d = self.plot_params['x_max'] - self.plot_params['x_min']
        self.plot_params['x_max'] += d
        self.build_plot_data(self.plot_canvas)

    def update_plot(self):
        self.build_plot_data(self.plot_canvas)


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, number, parent=None, width=5, height=4, dpi=100):
        self.number = number
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.__ax1 = fig.add_subplot(111)
        self.__ax2 = self.__ax1.twinx()
        self.__ax3 = self.__ax1.twinx()
        self.__ax4 = self.__ax1.twinx()
        fig.subplots_adjust(right=0.9)
        super(MplCanvas, self).__init__(fig)
        self.__plot = None

    def get_plot(self):
        return self.__plot

    def set_plot(self, plot):
        self.__plot = plot
        self.__plot.attach(self.__ax1, self.__ax2, self.__ax3, self.__ax4, self.figure)


class BigPlotWindow(QMainWindow):

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Monitor")
        layout = QVBoxLayout()
        self.canvas = MplCanvas(-1, self)
        nav_bar = NavigationToolbar(self.canvas, self)
        nav_bar.setMovable(False)
        self.addToolBar(Qt.BottomToolBarArea, nav_bar)
        layout.addWidget(self.canvas)
        # self.setLayout(layout)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.plot = None
        self.number = 0

    def set_plot(self, plot):
        self.canvas.set_plot(plot)
        self.plot = plot



class TableWin(QWidget):

    def __init__(self, df1, df2, object_data):
        super(TableWin, self).__init__()
        self.object_data = object_data
        self.table = QTableView(self)
        self.df = pd.concat([
            df1[['time', 'input_voltage', 'voltage', 'input_current', 'current', 'input_temperature', 'temperature'
                 ]].rename(columns={'time': 'time 1', 'input_voltage': 'input voltage 1', 'voltage': 'voltage 1',
                                    'input_temperature': 'input temperature 1', 'temperature': 'temperature 1',
                                    'input_current': 'input current 1', 'current': 'current 1'}),
            df2[['time', 'input_voltage', 'voltage', 'input_current', 'current', 'input_temperature', 'temperature'
                 ]].rename(columns={'time': 'time 2', 'input_voltage': 'input voltage 2', 'voltage': 'voltage 2',
                                    'input_temperature': 'input temperature 2', 'temperature': 'temperature 2',
                                    'input_current': 'input current 2', 'current': 'current 2'})
        ], axis=1)
        if self.df['temperature 2'].hasnans:
            self.df = self.df.drop(columns=['temperature 2', 'input temperature 2'])
        elif self.df['temperature 1'].hasnans:
            self.df = self.df.drop(columns=['temperature 1', 'input temperature 1'])
        self.model = TableModel(self.df.round(2))
        self.table.setModel(self.model)
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)


class DateDialog(QDialog):
    def __init__(self, parent=None):
        super(DateDialog, self).__init__(parent)

        layout = QVBoxLayout(self)

        # nice widget for editing the date
        self.datetime = QDateEdit(self)
        self.datetime.setCalendarPopup(True)
        self.datetime.setDate(QDate.currentDate())
        layout.addWidget(self.datetime)

        # OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # get current date and time from the dialog
    def date(self):
        return self.datetime.date()

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def getDate(parent=None):
        dialog = DateDialog(parent)
        result = dialog.exec_()
        date = dialog.date()
        return (date.getDate(), result == QDialog.Accepted)
