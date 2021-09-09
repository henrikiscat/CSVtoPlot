import pandas as pd
import re
import time

import pandas.errors

ignored_columns = ['Test', 'Cell', 'Rack', 'Shelf', 'Position', 'Cell ID', 'Load On time', 'Step Time (Seconds)']

ignored_reasoncodes = [1, 2, 5, 30]

reason_codes = {0: '?', 1: 'DeltaV', 2: 'DeltaTime', 3: 'EndEvent', 4: 'NewEvent', 5: 'DeltataI', 6: 'VEnd', 7: 'TimeEnd',
                8: 'MeasurmentStoppedByUser',
                9: 'DynamicMemoryAllocation Failure', 10: 'IEnd', 11: 'VMax', 12: 'VMin', 13: 'VCharge', 14: 'AHCharge', 15: 'AHDisChg',
                16: 'Pause', 17: 'MaxPowerReached', 18: 'PIError', 19: 'TPowerMOSFET', 20: 'TShunt50A', 21: 'TShunt5A',
                22: 'T24VMOSFET', 23: 'T96VMOSFET', 24: 'TDishchrMOSFET', 25: 'Ilimit', 26: 'TestEnd', 27: 'TempMin',
                28: 'TempMax', 29: 'Parallel Switching Failure', 30: 'AuxData', 31: 'DCRes', 32: 'ACRes',
                33: 'First measurement after recovery from power failure', 34: 'Output Error',
                35: 'Health check error', 36: 'Climate Control error', 37: 'Failed AC Internal Impedance',
                38: 'Front CAN bus Off error', 39: 'Interal CAN bus Off error',
                40: 'CEIDI error',
                42: 'CEIDKeepAliveError', 45: 'Manual Pause', 46: 'Resumed', 47: 'ResumedCS', 100: 'VauxMax',
                101: 'VauxMin', 102: 'EndDeltaV', 103: 'TimeChargeEnd',
                104: 'TimeDischargeEnd', 105: 'CellVoltMin', 106: 'CellVoltMax' , 107: 'CurrentDischargeEnd',
                108: 'PreassureMax', 109: 'TempIncrease', 110: 'TestTempReached',
                111: 'DeltaVpositive', 112: 'DeltaVnegative', 114: 'Balanced', 113: 'UnBalanced', 115: 'CVMax',
                116: 'CVMin', 117: 'VMin_StdCycle',
                118: 'CellVoltMin_StdCycle', 119: 'VMin_C_20',
                120: 'CellVoltMin_C_20'}

skip_testinfo = ['Default', '<NONE>', 'Other', 'G']


def find_rows(file):
    print("Filename: {}".format(file))
    timeout = 3
    start_timer = time.time()
    row_index = 0
    start = row_index
    skip = False
    position_context = False
    sections = {'indices'
                : [], 'index': '', 'context_log': [], 'split_results': {}}
    with open(file, 'r') as cf:
        while True:
            if time.time() - start_timer >= timeout:
                raise TimeoutError
            line = cf.readline()
            if "CONTEXT" in line:
                if "END" not in line:
                    position_context = True
                else:
                    position_context = False
            line_length = len(line.split(','))
            if row_index == 0:
                prev_length = line_length
            if "Split Results" in line:
                print("This is a Split Results -line")
                splitted_line = line.split(",")
                sections["split_results"] = {"Results": splitted_line[1].split()[2],
                                             "Part": splitted_line[2].split()[1]}
                skip = True
            elif line_length != prev_length and not skip:
                if ',' in line:
                    if line_length > 17:
                        print('Data row: {}'.format(line))
                        sections['indices'].append(range(start, row_index - 1))
                        for x in line.split(','):
                            if 'Total Time' in x:
                                sections['index'] = x
                                print("Found last section, Row: {}, Content: {}".format(row_index, line))
                                sections['context_log'].append(position_context)
                                return sections, row_index
                    print("New section found! Last row: {}, Content: {}, Is Context: {}".format(row_index -1, line, position_context))
                    sections['indices'].append(range(start, row_index - 1))
                    sections['context_log'].append(position_context)
                    start = row_index
                    prev_length = line_length
            elif skip:
                prev_length = line_length
                start = row_index
                skip = False
            row_index += 1


def rename(col_name):
    return re.sub('\)', ']', re.sub('\(', '[', col_name))


def format_time(df_data, format):
    sr_index = pd.Series(df_data['Total Time [Hours in hh:mm:ss.xxx]'])
    df_index = sr_index.str.split(r"(\d{1,3}):(\d{2}):(\d{2}).(\d{3})", expand=True)
    if format == 'h':
        return df_index[1].values
    elif format == 's':
        df_index['s'] = df_index[1].astype('int')*3600 + df_index[2].astype('int')*60 + df_index[3].astype('int')
        return df_index['s'].values
    elif format == 'ms':
        df_index['ms'] = df_index[1].astype('int')*3600000 + df_index[2].astype('int')*60000 + \
                         df_index[3].astype('int')*1000 + df_index[4].astype('int')
        return pd.to_timedelta(df_index['ms'], 'ms')


def file_to_df(_csv_file, window):
    try:
        sections, header_row = find_rows(_csv_file)
        data = []
        for i in range(len(sections['indices'])):
            data.append(pd.read_csv(_csv_file, skiprows=lambda x: x not in sections['indices'][i], comment='#',
                                    squeeze=True,
                                    header=None))
        testinfo = pd.Series(data[0][1].values, data[0][0].values).dropna(axis=0, how='all')
        #testinfo = testinfo.filter(like='St', axis=0)
        print(testinfo.to_dict())
        start = pd.to_datetime(testinfo.get('Start Time:'), infer_datetime_format=True)
        df_data = pd.read_csv(_csv_file, skiprows=header_row, index_col=False).dropna(axis=1, how='all')
        df_data.columns = [rename(x) for x in df_data.columns]
        time_delta = format_time(df_data, 'ms')
        df_data.index = start.to_datetime64().repeat(df_data.shape[0]) + time_delta
        df_data.index.name = 'Total Time'
        df_data['ReasonCode Name'] = [reason_codes[x] for x in df_data['ReasonCode'].values.tolist()]
        window.write_event_value('-FILE TO DF-', [data, df_data, sections, testinfo])
    except TimeoutError:
        window.write_event_value('-FILE TO DF EXCEPTION-',
                                 "Filindexeringen tog för lång tid, filen är förmodligen felformaterad")

