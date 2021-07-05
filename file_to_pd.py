import pandas as pd
import re

ignored_columns = ['Test', 'Cell', 'Rack', 'Shelf', 'Position', 'Cell ID', 'Load On time', 'Step Time (Seconds)']

reason_codes = {1: 'DeltaV', 2: 'DeltaT', 3: 'EndEvent', 4: 'NewEvent', 5: 'Deltatal', 6: 'VEnd', 7: 'TEnd', 8: 'MEnd',
                9: 'DMAEnd', 10: 'IEnd', 11: 'VMax', 12: 'VMin', 13: 'VCharge', 14: 'AHCharge', 15: 'AHDisChg',
                16: 'Pause', 17: 'MaxPower', 18: 'PIError', 19: 'TPowerMOSFET', 20: 'TShunt50A', 21: 'TShunt5A',
                22: 'T24VMOSFET', 23: 'T96VMOSFET', 24: 'TDishchrMOSFET', 25: 'Ilim', 26: 'TestEnd', 27: 'TempMin',
                28: 'TempMax', 29: 'PllFailure', 30: 'AuxData', 31: 'DCRes', 32: 'ACRes', 33: 'PowerUp', 34: 'OError',
                35: 'HCError', 36: 'CCError', 37: 'ACResFailure', 38: 'FCBOffError', 39: 'ICBOffError',
                40: 'CEIDIError',
                42: 'CEIDKeepAliveError', 100: 'VauxMax', 101: 'VauxMin', 102: 'EndDeltaV', 103: 'TimeChargeEnd',
                104: 'TimeDischargeEnd', 105: 'CellVoltMin', 106: 'CellVoltMax' , 107: 'CurrentDischargeEnd',
                108: 'PreassureMax', 109: 'TempIncrease', 110: 'TestTempReached',
                111: 'DeltaVpositive', 112: 'DeltaVnegative', 114: 'Balanced', 113: 'UnBalanced', 115: 'CVMax',
                116: 'CVMin', 117: 'VMin_StdCycle',
                118: 'CellVoltMin_StdCycle', 119: 'VMin_C_20',
                120: 'CellVoltMin_C_20'}


def find_rows(file):
    row_index = 0
    start = row_index
    sections = {'indices'
                : [], 'index': ''}
    with open(file, 'r') as cf:
        while True:
            line = cf.readline()
            line_length = len(line.split(','))
            if row_index == 0:
                prev_length = line_length
            if line == '\n':
                print("Found empty line! #{}".format(row_index))
                pass
            elif line_length != prev_length:
                if ',' in line:
                    if line_length > 17:
                        print('Data row: {}'.format(line))
                        sections['indices'].append(range(start, row_index - 1))
                        for x in line.split(','):
                            if 'Total Time' in x:
                                sections['index'] = x
                                print("Found last section, Row: {}, Content: {}".format(row_index, line))
                                return sections, row_index
                    print("New section found! Last row: {}, Content: {}".format(row_index, line))
                    sections['indices'].append(range(start, row_index - 1))
                    start = row_index
                    prev_length = line_length
                else:
                    pass
            row_index += 1


def rename(col_name):
    return re.sub('\)', ']', re.sub('\(', '[', col_name))


def file_to_df(_csv_file, window):
    sections, header_row = find_rows(_csv_file)
    data = []
    for index_range in sections['indices']:
        data.append(pd.read_csv(_csv_file, skiprows=lambda x: x not in index_range, comment='#', squeeze=True,
                                header=None))
    print("Header row: {}".format(header_row))
    df_data = pd.read_csv(_csv_file, skiprows=header_row, index_col=sections['index'])
    df_data.columns = [rename(x) for x in df_data.columns]
    df_data.index.name = rename(df_data.index.name)
    window.write_event_value('-FILE TO DF-', [data, df_data])
