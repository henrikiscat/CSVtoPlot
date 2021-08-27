import time

import xlsxwriter


def formatter(writer, columns, header_format, cell_format, worksheet, start_row):
    j = 0
    for i in columns:
        split = i.split('[')
        if len(split) > 1:
            text = split[0] + '\n[' + split[-1]
        else:
            text = i
        worksheet.write(start_row, j, text, header_format)
        if j > 1:
            worksheet.set_column(j, j, len(split[0]) + 1, cell_format)
        j += 1


def export_data(window, filetype, df_data_, data, filename, df_data, pd, color, accumulate):
    df_start = df_data[0]
    start_row = df_start.shape[0] + 3
    tic = time.process_time()

    if filetype == "excel":
        try:
            filename = filename + '.xlsx'
            writer = pd.ExcelWriter(filename, engine='xlsxwriter', )

            if len(df_data) > 1:
                context = df_data[1]
                context.to_excel(writer, sheet_name="Context Switching", index=None, header=False )

            if accumulate is not None:
                try:
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
                    accumulated.to_excel(writer, sheet_name="Accumulated", index=None, header=True)
                except Exception as e:
                    print(
                        "Ett fel inträffade vid insamling av ackumulerad data, innehåller dokumentet en \"Accumulated\" -flik? Error: {}".format(
                            e))
            data_ = df_data_[data]
            data_ = data_.dropna(axis=1, how='all')
            data_.to_excel(writer, sheet_name='Data', startcol=0, startrow=start_row, header=True, engine=xlsxwriter)
            workbook = writer.book
            worksheet = writer.sheets['Data']
            header_format = workbook.add_format({'bold': True, 'valign': 'top',
                                                 'fg_color': color,
                                                 'border': 0, 'align': 'center'})
            header_format.set_text_wrap()
            info_format = workbook.add_format({'bold': True, 'align': 'left', 'fg_color': color})
            left_aligned = workbook.add_format({'align': 'left'})
            cell_format = workbook.add_format()
            cell_format.set_align('center')
            row = 0
            for item in df_start[0].values.tolist():
                worksheet.write(row, 0, item, info_format)
                row += 1

            df_charge = pd.DataFrame()
            df_discharge = pd.DataFrame()
            for i in range(df_data_['Cycle'].min(), df_data_['Cycle'].max()):
                ndf = df_data_[df_data_['Cycle'] == i].nlargest(1, 'Charge Capacity [mAh]')
                mdf = df_data_[df_data_['Cycle'] == i].nlargest(1, 'Discharge Capacity [mAh]')
                if ndf.loc[:, 'Charge Capacity [mAh]'].values[0] > 0:
                    df_charge = df_charge.append(ndf)
                if mdf.loc[:, 'Discharge Capacity [mAh]'].values[0] > 0:
                    df_discharge = df_discharge.append(mdf)
            df_charge = df_charge.dropna(axis=1, how='all')
            df_discharge = df_discharge.dropna(axis=1, how='all')
            df_charge.to_excel(writer, sheet_name="Charge", header=True)
            df_discharge.to_excel(writer, sheet_name="Discharge", header=True)
            row = 0
            for item in df_start[1].values.tolist():
                try:
                    worksheet.write(row, 1, item, left_aligned)
                except TypeError:
                    pass
                row += 1
            worksheet.set_column(0, 0, len(max(df_start[0], key=len)))

            formatter(writer, [data_.index.name] + data_.columns.tolist(), header_format, cell_format, worksheet, start_row)

            formatter(writer, [df_charge.index.name] + df_charge.columns.tolist(), header_format, cell_format,
                      writer.sheets['Charge'], 0)

            formatter(writer, [df_discharge.index.name] + df_discharge.columns.tolist(), header_format, cell_format,
                      writer.sheets['Discharge'], 0)

            writer.save()
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
