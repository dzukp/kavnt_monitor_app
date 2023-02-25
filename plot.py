import pandas as pd
import numpy as np
import matplotlib.dates as mdates
from matplotlib.ticker import AutoMinorLocator, MaxNLocator, NullLocator, FixedLocator,  EngFormatter, LinearLocator
from datetime import datetime


class PlotProperties:
    def __init__(self):
        self.em2_shift = 0
        self.show_corrected = True
        self.show_extra_pen = False
        self.x_min = None
        self.x_max = None
        self.show_legend = False

    def reset(self):
        self.__init__()


class Plot:
    def __init__(self):
        self.df = None
        self.ax1 = None
        self.ax2 = None
        self.ax3 = None
        self.ax4 = None
        self.figure = None
        self.voltage_limits = (7, 17)
        self.current_limits = (-25, 25)
        self.temperature_limits = (0, 60)

    def attach(self, ax1, ax2, ax3, ax4, figure):
        self.ax1 = ax1
        self.ax2 = ax2
        self.ax3 = ax3
        self.ax4 = ax4
        self.figure = figure

    def configure(self, config):
        self.voltage_limits = config.get('Plot', f'volt_min_limit'), config.get('Plot', f'volt_max_limit')
        self.current_limits = config.get('Plot', f'current_min_limit'), config.get('Plot', f'current_max_limit')
        self.temperature_limits = config.get('Plot', f'temperature_min_limit'), config.get('Plot', f'temperature_max_limit')

    def prepare(self, df):
        if df is None:
            df = self.df
        else:
            self.df = df
        for i in range(len(self.ax1.lines)):
            del self.ax1.lines[0]
        for i in range(len(self.ax2.lines)):
            del self.ax2.lines[0]
        for i in range(len(self.ax3.lines)):
            del self.ax3.lines[0]
        for i in range(len(self.ax4.lines)):
            del self.ax4.lines[0]
        return df

    def set_ticks(self):
        self.ax1.xaxis.set_major_locator(LinearLocator(2))
        self.ax1.xaxis.set_minor_locator(AutoMinorLocator())
        self.ax2.yaxis.set_major_locator(LinearLocator(2))
        self.ax1.yaxis.set_major_locator(LinearLocator(11))
        self.ax4.yaxis.set_major_locator(LinearLocator(11))

        v_formmatter = EngFormatter(unit='V')
        t_formmatter = EngFormatter(unit=u'\u00b0C')
        perc_formmatter = EngFormatter(unit='%')
        amp_formmatter = EngFormatter(unit='A')
        time_formatter = mdates.DateFormatter('%d.%m %H:%M')
        time_formatter_minor = mdates.DateFormatter('%H:%M')

        # self.ax1.set_ylabel('V', loc='top')
        # self.ax2.set_ylabel(u'\u00b0C', loc='top')

        self.ax1.yaxis.set_major_formatter(v_formmatter)
        self.ax2.yaxis.set_major_formatter(t_formmatter)
        self.ax4.yaxis.set_major_formatter(amp_formmatter)

        self.ax1.xaxis.set_major_formatter(time_formatter)
        self.ax1.xaxis.set_minor_formatter(time_formatter_minor)

        self.ax3.yaxis.set_major_formatter(perc_formmatter)
        self.ax3.xaxis.set_major_formatter(time_formatter)
        self.ax3.xaxis.set_minor_formatter(time_formatter_minor)

    def create_plot(self, df, title, plot_properties):
        df = self.prepare(df)
        voltage_field = 'voltage'  # if plot_properties.show_corrected else 'input_voltage'
        temp_field = 'temperature'  # if plot_properties.show_corrected else 'input_temperature'
        current_field = 'current'  # if plot_properties.show_corrected else 'input_current'
        # p11 = self.ax1.step(df['dtime'], df['max_charging_voltage'], '--', color='red', label='Max charging volt.')
        # p13 = self.ax2.step(df['dtime'], df['ideal_temp'], '--', color='green', label='25C')
        # p14 = self.ax3.step(df['dtime'], df['capacity'], color='blue', label='Capacity')
        p16 = self.ax4.step(df['dtime'], df[current_field], color='magenta', label='Current')
        p12 = self.ax2.step(df['dtime'], df[temp_field], color='green', label='Temperature')
        p15 = self.ax1.step(df['dtime'], df[voltage_field], color='red', label='Voltage')

        self.ax1.set_ylim(*self.voltage_limits)
        self.ax2.set_ylim(*self.temperature_limits)
        self.ax4.set_ylim(*self.current_limits)
        if plot_properties.show_extra_pen:
            self.ax3.set_xlim(0, 100)

        x_min, x_max = df['dtime'].iloc[[0, -1]].values
        for ax in (self.ax1, self.ax2, self.ax3, self.ax4):
            ax.set_xlim(x_min, x_max)

        self.set_ticks()

        if plot_properties.show_extra_pen:
            # legend_list = (p11 + p12 + p13 + p14 + p15 + p16)
            legend_list = (p12 + p15 + p16)
        else:
            legend_list = (p12 + p15 + p16)

        self.ax2.get_yaxis().set_visible(True)
        self.ax3.get_yaxis().set_visible(False)

        self.ax2.spines["right"].set_position(("outward", 30))

        self.ax1.grid(True, which='both')
        # self.ax4.grid(True, which='major')
        for ax in (self.ax1, self.ax2, self.ax3, self.ax4):
            ax.tick_params(axis='both', which='both', labelsize=6)
        # self.ax3.legend(loc='best', bbox_to_anchor=(0., 0., 1., 1.), handles=legend_list).set_visible(
        #     plot_properties.show_legend)
        self.figure.suptitle(title)
        self.figure.tight_layout()


class BigPlot(Plot):

    def create_plot(self, df, title, plot_properties):
        if df is None:
            return

        df = df.copy()

        time_shift = plot_properties.em2_shift

        for i in range(len(self.ax1.lines)):
            del self.ax1.lines[0]
        for i in range(len(self.ax2.lines)):
            del self.ax2.lines[0]
        for i in range(len(self.ax3.lines)):
            del self.ax3.lines[0]
        for i in range(len(self.ax4.lines)):
            del self.ax4.lines[0]

        voltage_field = 'voltage' if plot_properties.show_corrected else 'input_voltage'
        temp_field = 'temperature' if plot_properties.show_corrected else 'input_temperature'
        current_field = 'current' if plot_properties.show_corrected else 'input_current'

        self.ax3.axis('on' if plot_properties.show_extra_pen else 'off')
        # self.ax4.axis('on' if plot_properties.show_extra_pen else 'off')

        if plot_properties.show_extra_pen:
            p11 = self.ax1.step(df['dtime'], df['max_charging_voltage'], '--', color='red',
                                label='Max charging volt. 1')
            p13 = self.ax2.step(df['dtime'], df['ideal_temp'], '--', color='green', label='25C')
            p14 = self.ax3.step(df['dtime'], df['capacity'], color='blue', label='Capacity')
        p16 = self.ax4.step(df['dtime'], df[current_field], color='magenta', label='Current')
        p12 = self.ax2.step(df['dtime'], df[temp_field], color='green', label='Temperature')
        p15 = self.ax1.step(df['dtime'], df[voltage_field], color='red', label='Voltage')

        # if plot_properties.show_extra_pen:
        #     p21 = self.ax1.step(df2['dtime'], df2['max_charging_voltage'], '--', color='orange',
        #                        label='Max charging volt. 2')
        #     # self.ax2.step(df2['dtime'], df2['ideal_temp'], '.', color='lime', label='25C')
        #     p23 = self.ax3.step(df2['dtime'], df2['capacity'], color='cyan', label='Capacity 2')
        # p25 = self.ax4.step(df2['dtime'], df2[current_field], color='violet', label='Current')
        # # p22 = self.ax2.step(df2['dtime'], df2[temp_field], color='lime', label='Temperature 2')
        # p24 = self.ax1.step(df2['dtime'], df2[voltage_field], color='orange', label='Voltage 2')

        self.ax2.spines["right"].set_position(("outward", 40))

        self.ax1.set_ylim(*self.voltage_limits)
        self.ax2.set_ylim(*self.temperature_limits)
        self.ax4.set_ylim(*self.current_limits)
        self.ax3.set_xlim(0, 100)

        if plot_properties.x_min is None:
            x_min = np.concatenate([df['dtime'].values]).min()
            x_max = np.concatenate([df['dtime'].values]).max()
        else:
            x_min = plot_properties.x_min
            x_max = plot_properties.x_max
        self.ax1.set_xlim(x_min, x_max)
        self.ax2.set_xlim(x_min, x_max)
        self.ax4.set_xlim(x_min, x_max)
        if plot_properties.show_extra_pen:
            self.ax3.set_xlim(x_min, x_max)

        self.set_ticks()

        if plot_properties.show_extra_pen:
            # self.ax3.set_ylabel('%', loc='top')
            legend_list = (p11 + p12 + p13 + p14 + p15 + p16)
        else:
            legend_list = (p12 + p15 + p16)
        self.ax3.legend(loc='best', bbox_to_anchor=(0., 0., 1., 1.), handles=legend_list).set_visible(True)
        self.ax1.grid(True, which='both')
        self.figure.suptitle(title)
        self.figure.tight_layout()
