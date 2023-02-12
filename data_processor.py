from datetime import datetime, timedelta

import pandas as pd


class DataProcessor:

    def __init__(self, count):
        self.columns = ['dtime', 'temperature', 'voltage', 'current']
        self.dfs = [pd.DataFrame(data=[], columns=self.columns) for i in range(count)]

    def add_data(self, idx, data):
        df = self.dfs[idx]
        values = [data.get(c) for c in self.columns]
        values[0] = datetime.now()
        df_data = pd.DataFrame(data=[values], columns=self.columns)
        df_data = self.calc_extra_data(df_data)
        df = pd.concat([df, df_data])
        self.dfs[idx] = df

    def calc_extra_data(self, df):
        def capacity(data):
            if data >= 13.0:
                return 100
            if data <= 11.6:
                return 0
            return round(66.67 * (data - 11.5))

        df['temperature'] = df.apply(lambda x: x['temperature'] if x['temperature'] != -50 else None, axis=1)
        df['ideal_temp'] = 25.0
        df['max_charging_voltage'] = df['temperature'].apply(
            lambda x: 15.4 - 0.03 * (x if (x is not None) and (x > -40) else 0))
        df['capacity'] = df['voltage'].apply(capacity)
        return df

    def get_data(self, idx):
        start_time = datetime.now() - timedelta(hours=12)
        df = self.dfs[idx]
        return df[df['dtime'] > start_time]
