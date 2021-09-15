import time

import pandas as pd
import xlsxwriter


def formatter(columns, second_row, header_format, cell_format, worksheet, start_row, time_column):
    j = 0
    for i in range(len(columns)):
        split = columns[i].split('[')
        if len(split) > 1:
            text = split[0] + '\n[' + split[-1]
        else:
            text = columns[i]
        worksheet.write(start_row, j, text, header_format)
        if j > 1 or time_column:
            width = max([len(x) for x in split])
            if second_row is not None:
                width = max([width, len(second_row[i])])
            worksheet.set_column(j, j, width + 1, cell_format)
        j += 1


def charge_tab(df_data_, pd):
    df_charge = pd.DataFrame()
    cycle_max = df_data_['Cycle'].max()
    cycle_min = df_data_['Cycle'].min()
    if cycle_max == cycle_min:
        cycle_range = [cycle_max]
    else:
        cycle_range = range(cycle_min, cycle_max)
    for i in cycle_range:
        ndf = df_data_[df_data_['Cycle'] == i].nlargest(1, 'Charge Capacity [mAh]')
        if ndf.loc[:, 'Charge Capacity [mAh]'].values[0] > 0:
            df_charge = df_charge.append(ndf)
    df_charge = df_charge.dropna(axis=1, how='all')
    return df_charge


def discharge_tab(df_data_, pd):
    df_discharge = pd.DataFrame()
    cycle_max = df_data_['Cycle'].max()
    cycle_min = df_data_['Cycle'].min()
    if cycle_max == cycle_min:
        cycle_range = [cycle_max]
    else:
        cycle_range = range(cycle_min, cycle_max)
    for i in cycle_range:
        mdf = df_data_[df_data_['Cycle'] == i].nlargest(1, 'Discharge Capacity [mAh]')
        if mdf.loc[:, 'Discharge Capacity [mAh]'].values[0] > 0:
            df_discharge = df_discharge.append(mdf)
    df_discharge = df_discharge.dropna(axis=1, how='all')
    return df_discharge


def accumulate_tab(df_data_, pd, accumulate):
    accumulated = pd.read_excel(accumulate, sheet_name="Accumulated")
    x = round(accumulated.iloc[2, 0])
    y = accumulated.iloc[3, 0]
    if isinstance(y, int):
        accumulated_cyclenr = x if x > round(y) else round(y)
    else:
        accumulated_cyclenr = x
    print(accumulated_cyclenr)
    df_data_cyclecont = df_data_.copy()
    df_data_cyclecont.loc[:, 'Cycle'] = df_data_['Cycle'] + accumulated_cyclenr + 1
    df_data_ = df_data_cyclecont
    return df_data_, accumulated


def context_tab(df_data, writer, header_format, cell_format, pd):
    context = df_data[1]
    context = context.dropna(axis=1)
    print("Before: {}".format(context.dtypes))
    print(context.convert_dtypes().dtypes)
    context.to_excel(writer, sheet_name="Context Switching", index=None, header=False)
    formatter(context.iloc[0, :].values, context.iloc[1, :].values, header_format, cell_format, writer.sheets['Context Switching'], 0, None)


def export_maccor(window, filetype, data, filename, test_info, color):
    tic = time.process_time()
    if filetype == "excel":
        try:
            filename = filename + '.xlsx'
            data.index = [f'{x//(3600*1000):02d}:{x%(3600*1000)//(1000*60):02d}' for x in data.index.values.tolist()]

            data.index.name = 'Total Time [hh:mm]'
            with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                workbook = writer.book
                header_format = workbook.add_format({'bold': True, 'valign': 'top',
                                                 'fg_color': color,
                                                 'border': 0, 'align': 'center'})
                header_format.set_text_wrap()

                #info_format = workbook.add_format({'bold': True, 'align': 'left', 'fg_color': color})
                #left_aligned = workbook.add_format({'align': 'left'})
                cell_format = workbook.add_format()
                data.to_excel(writer, sheet_name='Data')
                worksheet = writer.sheets['Data']
                window.write_event_value('-EXPORT MACCOR-', 'APAN')
                formatter([data.index.name] + data.columns.tolist(), None, header_format, cell_format, worksheet,
                        0,
                        False)
        except PermissionError as e:
            window.write_event_value('-EXPORT EXCEPTION-',
                                         "Det gick inte att skriva till filen. Är den öppnad?: {}".format(e))
            return
    elif filetype == "text":
        window.write_event_value('-EXPORT EXCEPTION-', "Exporteraren för texfiler är inte färdig ännu")
        return
    elif filetype == "html":
        window.write_event_value('-EXPORT EXCEPTION-', "Exporteraren för htmlfiler är inte färdig ännu")
        return
    toc = time.process_time()
    total_time = toc - tic
    window.write_event_value('-EXPORT DONE-',
                             "Exporten tog: {} minuter och {} sekunder".format(round(total_time // 60),
                                                                                   round(total_time % 60)))


def export_pec(window, filetype, df_data_, data, filename, df_data, pd, color, accumulate, test_info):
    df_start = df_data[0]
    start_row = df_start.shape[0] + 3
    tic = time.process_time()
    if filetype == "excel":
        row = 0
        try:
            filename = filename + '.xlsx'
            with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                #df_data_.dropna(axis=1, how='all')
                data_ = df_data_[data]
                data_ = data_.dropna(axis=1, how='all')
                workbook = writer.book
                header_format = workbook.add_format({'bold': True, 'valign': 'top',
                                                 'fg_color': color,
                                                 'border': 0, 'align': 'center'})
                header_format.set_text_wrap()
                info_format = workbook.add_format({'bold': True, 'align': 'left', 'fg_color': color})
                left_aligned = workbook.add_format({'align': 'left'})
                cell_format = workbook.add_format()
                cell_format.set_align('center')
                if len(df_data) > 1:
                    context_tab(df_data, writer, header_format, cell_format, pd)
                data_.to_excel(writer, sheet_name='Data', startcol=0, startrow=start_row, header=True, engine=xlsxwriter)
                worksheet = writer.sheets['Data']
                if accumulate is not None:
                    df_data_ = accumulate_tab(df_data_, accumulate)
                #for item in df_start[0].values.tolist():
                 #   worksheet.write(row, 0, item, info_format)
                  #  row += 1

                #rint("test_info: {}".format(test_info))
                for key, value in test_info.items():
                    worksheet.write(row, 0, key, info_format)
                    worksheet.write(row, 1, value, left_aligned)
                    row += 1
                if 'Charge Capacity [mAh]' in df_data_.columns.values.tolist():
                    df_charge = charge_tab(df_data_, pd)
                    df_charge.to_excel(writer, sheet_name="Charge", header=True)
                    formatter([df_charge.index.name] + df_charge.columns.tolist(), None, header_format, cell_format,
                              writer.sheets['Charge'], 0, True)
                if 'Discharge Capacity [mAh]' in df_data_.columns.values.tolist():
                    df_discharge = discharge_tab(df_data_, pd)
                    df_discharge.to_excel(writer, sheet_name="Discharge", header=True)
                    formatter([df_discharge.index.name] + df_discharge.columns.tolist(), None, header_format, cell_format,
                              writer.sheets['Discharge'], 0, True)
                row = 0
                #for item in df_start[1].values.tolist():
                 #   try:
                  #      worksheet.write(row, 1, item, left_aligned)
                   # except TypeError:
                    #    pass
                   # row += 1
                worksheet.set_column(0, 0, len(max(df_start[0], key=len)))
                formatter([data_.index.name] + data_.columns.tolist(), None, header_format, cell_format, worksheet, start_row,
                          False)
                if accumulate is not None:
                    df_data_, accumulated = accumulate_tab(df_data, pd, accumulate)
                    accumulated.to_excel(writer, sheet_name="Accumulated", index=None, header=True)
        except PermissionError as e:
            window.write_event_value('-EXPORT EXCEPTION-',
                                     "Det gick inte att skriva till filen. Är den öppnad?: {}".format(e))
            return
    elif filetype == "text":
        filename = filename + '.txt'
        string_ = df_data_[data].to_string()
        with open(filename, 'w') as f:
            f.write(string_)
    elif filetype == 'html':
        filename = filename + '.html'
        html = df_data_[data].to_html()
        with open(filename, 'w') as f:
            f.write(html)
    toc = time.process_time()
    total_time = toc - tic
    window.write_event_value('-EXPORT DONE-', "Exporten tog: {} minuter och {} sekunder".format(round(total_time // 60),
                                                                                                round(total_time % 60)))
