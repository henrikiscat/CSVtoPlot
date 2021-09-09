import pandas as pd

new_names = {'Cyc#': 'Cycle', 'Test (Min)': 'Test [min]', 'Step (Min)': 'Step Time [min]', 'Amp-hr': 'Amp-hr [Ah]',
             'Watt-hr': 'Watt-hr [Wh]', 'Amps': 'Current [A]', 'Volts': 'Voltage [V]'}

def rename_cols(df):
    return df.rename(columns=new_names)


def maccor_to_df(file, window):
    df = rename_cols(pd.read_table(file, skiprows=1, decimal=',', index_col='Test (Min)'))
    print("DONE!")
    window.write_event_value('-MACCOR TO DF-', df)
