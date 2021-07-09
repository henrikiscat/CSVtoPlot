import time


def export_data(window, filetype, df_data_, data, filename, df_start, pd, color):
    start_row = df_start.shape[0] + 3
    tic = time.process_time()
    if filetype == "excel":
        try:
            filename = filename + '.xlsx'
            writer = pd.ExcelWriter(filename, engine='xlsxwriter', )
            df_data_[data].to_excel(writer, sheet_name='Data', startcol=0, startrow=start_row, header=True)
            workbook = writer.book
            worksheet = writer.sheets['Data']
            #worksheet_charge = writer.sheets['Charge']
            header_format = workbook.add_format({'bold': True, 'valign': 'top',
                                                 'fg_color': color,
                                                 'border': 0, 'align': 'center'})
            header_format.set_text_wrap()
            info_format = workbook.add_format({'bold': True, 'align': 'left', 'fg_color': color})
            cell_format = workbook.add_format()
            cell_format.set_align('center')
            row = 0
            for item in df_start[0].values.tolist():
                worksheet.write(row, 0, item, info_format)
                row += 1
            row = 0

            for item in df_start[1].values.tolist():
                try:
                    worksheet.write(row, 1, item)
                except TypeError:
                    pass
                row += 1
            worksheet.set_column(0, 0, len(df_data_[data].index.name))
            j = 0
            for i in [df_data_[data].index.name] + df_data_[data].columns.tolist():
                split = i.split('[')
                if len(split) > 1:
                    text = split[0] + '\n[' + split[-1]
                else:
                    text = i
                worksheet.write(start_row, j, text, header_format)
                worksheet.set_column(j, j, len(split[0]) + 1, cell_format)
                j += 1
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
