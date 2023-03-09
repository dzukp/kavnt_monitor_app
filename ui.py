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
    reset_plot = pyqtSignal(int)
    change_data_address = pyqtSignal(int, str)

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.cbox_plot_num = None
        self.edit_address = None
        self.addresses = {}
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
        # self.build_plot_data(self.plot_canvas)

    def init_ui(self):
        self.setWindowTitle("Monitor")
        # self.init_menu_bar()

        central_widget = QWidget()

        box = QVBoxLayout()
        grid_layout = QGridLayout()
        for i, plot in enumerate(self.plot_canvas):
            grid_layout.addWidget(plot, i // 3, i % 3)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 1)
        box.addLayout(grid_layout)
        control_layout = QVBoxLayout()
        grid_layout.addLayout(control_layout, 2, 2, alignment=Qt.AlignLeft)
        number_layout = QHBoxLayout()
        address_layout = QHBoxLayout()
        reset_layout = QHBoxLayout()

        self.cbox_plot_num = QComboBox()
        self.cbox_plot_num.addItems([str(i) for i in range(1, len(self.plot_canvas) + 1)])
        self.cbox_plot_num.currentTextChanged.connect(self.on_plot_number_changed)

        btn_reset = QPushButton('Reset')
        btn_reset.clicked.connect(self.on_reset_click)

        self.edit_address = QLineEdit()
        self.edit_address.setInputMask('HH:HH:HH:HH:HH:HH')
        self.edit_address.textEdited.connect(self.on_address_edited)

        control_layout.addLayout(number_layout)
        control_layout.addLayout(address_layout)
        control_layout.addLayout(reset_layout)

        number_layout.addWidget(QLabel('Plot number'))
        number_layout.addWidget(self.cbox_plot_num)
        number_layout.addStretch()
        address_layout.addWidget(QLabel('Address'))
        address_layout.addWidget(self.edit_address)
        address_layout.addStretch()
        reset_layout.addWidget(btn_reset)
        reset_layout.addStretch()
        control_layout.addStretch()

        # box.addLayout(control_layout)
        central_widget.setLayout(box)
        self.setCentralWidget(central_widget)
        # self.resize(800, 600)
        self.showMaximized()

    def init_menu_bar(self):
        menu_bar = self.menuBar()
        reset = QMenu("&Reset", self)
        menu_bar.addMenu(reset)
        for i, canvas in enumerate(self.plot_canvas):
            act = QAction(self)
            act.setText(f'Reset {i + 1}')
            reset.addAction(act)
            # act.triggered.connect

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

    def on_reset_click(self, evt):
        index = int(self.cbox_plot_num.currentText()) - 1
        self.reset_plot.emit(index)

    def on_data_address_changed(self, index, address):
        number = index + 1
        self.addresses[number] = address
        if self.cbox_plot_num.currentText() == str(number):
            self.edit_address.setText(address)

    def on_address_edited(self, text):
        number = int(self.cbox_plot_num.currentText())
        index = number - 1
        text = text.strip()
        if len(text) == 17 and self.addresses.get(number, '') != text:
            self.change_data_address.emit(index, text)

    def on_plot_number_changed(self, evt):
        number = int(self.cbox_plot_num.currentText())
        self.edit_address.setText(self.addresses.get(number, ''))

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
