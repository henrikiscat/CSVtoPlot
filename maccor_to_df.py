import pandas as pd
import re

new_names = {'Cyc#': 'Cycle', 'Test (Min)': 'Total Time', 'Step (Min)': 'Step Time [min]', 'Amp-hr': 'Amp-hr [Ah]',
             'Watt-hr': 'Watt-hr [Wh]', 'Amps': 'Current [A]', 'Volts': 'Voltage [V]', 'Aux #1': 'Ambient [\u00B0C]',
             'Aux #2': 'Terminal [\u00B0C]'}

types = {'Cycle': 'int', 'Total Time': 'int', 'Step Time [min]': 'float', 'Amp-hr [Ah]': 'float',
         'Watt-hr [Wh]': 'float',
         'Current [A]': 'float', 'Voltage [V]': 'float', 'Ambient [\u00B0C]': 'float', 'Terminal [\u00B0C]': 'float',
         'Rec#': 'float'}

ignored_columns = ['Units', 'Units.1']


def rename_cols(df):
    return df.rename(columns=new_names)


def maccor_to_df(file, window):
    with open(file) as f:
        line = f.readline()
        matches = re.match(r'.*(\d\d/\d\d/\d{4}).*(\d\d/\d\d/\d{4})\s*Filename:\s*(.*)\s*Procedure:'
                           r'\s*(.*)\s*Comment/Barcode:\s*(.*)\s*', line)
        test_info = pd.Series([pd.to_datetime(matches.group(1)), pd.to_datetime(matches.group(2)), matches.group(3), matches.group(4),
                               matches.group(5)], ['Today\'s Date:', 'Date of Test:', 'Filename:', 'Procedure:',
                                                   'Comment/Barcode:'],)

    df = pd.read_table(file, skiprows=1, decimal=',',
                       index_col=None)

    df = df.loc[:, (df != 0.0).any(axis=0)].select_dtypes(exclude=[
        'object'])
    df = rename_cols(df)
    df['Total Time'] = df['Total Time']*60*1000
    try:
        df = df.astype(types, errors='ignore')
    except KeyError:
        pass
    df = df.set_index('Total Time')
    window.write_event_value('-MACCOR TO DF-', (df, test_info))
