# This script was made to plot data found in CSV-format measurement data files generated by PEC (tm) test equipment
# Written by Henrik Isaksson 2021-05-07
import threading

from matplotlib import pyplot as plt

from file_to_pd import file_to_df
from maccor_to_df import maccor_to_df
from my_plotter import multiplot
from exporter import export_data
import pandas as pd
import PySimpleGUI as Sg
import time

ignored_columns = ['Test', 'Cell', 'Rack', 'Shelf', 'Position', 'Cell ID', 'Load On time', 'Step Time (Seconds)']
intertek_color = '#ffc700'
# Pattern of characters allowed in file naming, used with regular expression (re)
name_pattern = '[^a-öA-Ö0-9_]'
work_folder = ''
df_data = pd.DataFrame
df_context = pd.DataFrame
start = stop = pos = size = rows = 0
stop_busy = False
current_file = ""
test_info = pd.Series
data_type = ""


def busy_window(max_):
    layout_ = [[Sg.ProgressBar(max_, orientation='h', size=(15, 4), k='-PROGRESS BAR-')]]
    return Sg.Window(title="Detta kan ta en liten stund..", layout=layout_)


def busy_timer(window):
    markers = ['--', '\\', '|', '/', '--', '\\', '|', '/']
    while True:
        global stop_busy
        if stop_busy:
            break
        else:
            for mark in markers:
                window.write_event_value('-TIC-', mark)

                time.sleep(0.2)


def create_layout():
    left_column = [[Sg.Text("Datakolumner"), Sg.Button("Markera alla", k='-ALL-'), Sg.Button("Avmarkera alla",
                                                                                             k='-NONE-')],
                   [Sg.Listbox(values=[], size=(50, 30), enable_events=True, k='-COL-',
                               select_mode=Sg.LISTBOX_SELECT_MODE_MULTIPLE)],
                   [Sg.Text("Urval av data: ")],
                   [Sg.Slider(range=(1, 100), resolution=1, orientation='h', k='-DATA WINDOW SIZE-',
                              tooltip="Välj storlek på datafönster", default_value=100, enable_events=True),
                    Sg.Slider(range=(0, 100), resolution=1, orientation='h', k='-DATA WINDOW POSITION-',
                              tooltip="Välj datafönstrets position", default_value=50, enable_events=True)],
                   [Sg.Slider(range=(1, 100), resolution=1, orientation='h', k='-CYCLE MIN-',
                              tooltip='Välj undre cykelgräns', default_value=0, enable_events=True),
                    Sg.Slider(range=(1, 100), resolution=1, orientation='h', k='-CYCLE MAX-',
                              tooltip='Välj övre cykelgräns', enable_events=True)]]
    right_column = [[Sg.Table(values=[[' ', ' ']], headings=['Variabel', 'Värde'], k='-DESCRIPTION-',
                              col_widths=[20, 22], justification='left', auto_size_columns=False,
                              background_color="white", text_color="black",
                              size=(50, 17), alternating_row_color='light grey')],
                    [Sg.Table(values=[[' ', ' ', ' ']], headings=['Variabel', 'Värde', 'Enhet'], k='-UPDATE DETAILS-',
                              col_widths=[20, 17, 5], justification='left', auto_size_columns=False, size=(50, 17),
                              alternating_row_color='light grey', background_color="white", text_color="black")]]
    main_layout = [[Sg.Text("Öppna CSV-fil    ",), Sg.Input(key='-FILE-', visible=False, enable_events=True),
                    Sg.FileBrowse(file_types=(('ALL Files', '*.csv'),),
                                  ),
                    Sg.Text("Arbetskatalog"), Sg.Input(key='-WORK FOLDER-', visible=True, enable_events=True),
                    Sg.FolderBrowse(
                        )
                    ], [Sg.Text("Öppna Maccor-fil"), Sg.Input(key='-MACCOR FILE-', visible=False, enable_events=True),
                        Sg.FileBrowse(file_types=(('ALL Files', '*'),),
                                      )],
                   [Sg.Column(layout=left_column), Sg.Column(layout=right_column)],
                   [Sg.Checkbox("Rutmönster", k='-GRID-'), Sg.Button("Visa plot", key='-SHOW PLOT-'),
                    Sg.Combo(values=['-', '.-', '.'], default_value='-', k='-PLOT STYLE-'),
                    Sg.Text("Spara plot som:"),
                    Sg.Combo(values=['pdf'], default_value='pdf', readonly=True, enable_events=False,
                             key='-PLOT FILE TYPE-'), Sg.Button("Ok", key='-SAVE PLOT AS-'),
                    Sg.Text("Spara data som:"),
                    Sg.Combo(values=['excel', 'text', 'html'], default_value='excel', enable_events=False,
                             readonly=True, key='-FILE TYPE-'),
                    Sg.Checkbox("Resultat från föregående fil", key="-ACCUMULATE-"),
                    Sg.Button('Ok', key='-EXPORT FILE-')]]
    return main_layout


def main_window():
    global df_data, busy_id, cyclemin, cyclemax, cyclesetmax, cyclesetmin, current_file, data_type
    window = Sg.Window("Main window", create_layout())
    while True:
        global rows, pos, df_data, size, start, stop, work_folder, df_context, stop_busy, test_info
        event, values = window.read()
        if event == Sg.WINDOW_CLOSED:
            break
        elif event == "-SHOW PLOT-":
            window.set_cursor("watch")
            try:
                if data_type == "maccor":
                    title = "Maccor test"
                    # multiplot(df, values['-COL-'], values['-PLOT STYLE-'], False, '', values['-GRID-'], ())
                    data = df_data
                    test_info_ = None
                else:
                    df_start_dict = dict(data[0].values.tolist())
                    title = "Test ID: {}, {}, {}".format(df_start_dict['Test:'], df_start_dict['Test Description:'],
                                                         df_start_dict['TestRegime Suffix:'])
                    data = df_data[(df_data['Cycle'] >= cyclesetmin) & (df_data['Cycle'] <= cyclesetmax)]
                    test_info_ = data[0]
                # print(df_data[(df_data['Cycle'] > cyclesetmin) & (df_data['Cycle'] < cyclesetmax)])
                multiplot(data,
                          values['-COL-'], values['-PLOT STYLE-'], False, '',
                          values['-GRID-'], (17, 9), work_folder, test_info_, window, True, title, test_info)
            except (NameError, TypeError, IndexError) as err:
                window.set_cursor("arrow")
                Sg.PopupOK("Ingen data vald. \nError: {}".format(err), title="Ingen data")

        elif event == "-DATA WINDOW POSITION-":
            rows = df_data.shape[0]
            pos = round(values['-DATA WINDOW POSITION-'] * rows // 100)
            start = (lambda x: 0 if x < 0 else x)(int(pos - size / 2))
            stop = (lambda x: rows if x > rows else x)(int(pos + size / 2))
        elif event == "-DATA WINDOW SIZE-":
            rows = df_data.shape[0]
            size = round(values['-DATA WINDOW SIZE-'] * rows // 100)
            start = (lambda x: 0 if x < 0 else x)(int(pos - size / 2))
            stop = (lambda x: rows if x > rows else x)(int(pos + size / 2))
        elif event == '-FILE-':
            try:
                file = values['-FILE-']
                if file != current_file:
                    current_file = file
                    window.set_cursor("watch")
                    threading.Thread(target=file_to_df, args=(file, window), daemon=True).start()
                else:
                    pass
            except FileNotFoundError:
                window.set_cursor("arrow")
        elif event == '-MACCOR FILE-':
            window.set_cursor("watch")
            threading.Thread(target=maccor_to_df, args=(values['-MACCOR FILE-'], window)).start()
            #df_data = maccor_to_df(values['-MACCOR FILE-'])
            #window['-COL-'].Update(values=df_data.columns.tolist())

        elif event == '-EXPORT FILE-':
            if work_folder == '':
                Sg.popup_error('Ingen arbetskatalog vald.')
            else:

                accumulated_file = Sg.PopupGetFile("Välj fil att akumulera data från",
                                                   file_types=(('ALL Files', '*.xlsx'),)) if values["-ACCUMULATE-"] \
                    else None
                print("Accumulated file: {}".format(accumulated_file))
                threading.Thread(target=export_data, args=(window, values['-FILE TYPE-'], df_data.iloc[start:stop, :],
                                                           values['-COL-'], (work_folder + '/' + 'testfil'), data,
                                                           pd, intertek_color, accumulated_file, test_info,),
                                 daemon=True).start()
                window.set_cursor("watch")
        elif event == '-EXPORT EXCEPTION-':
            window.set_cursor('arrow')
            Sg.PopupError(values['-EXPORT EXCEPTION-'])
        elif event == '-SAVE PLOT AS-':
            if work_folder == '':
                Sg.popup_error('Ingen arbetskatalog är vald.')
            else:
                try:
                    window.set_cursor("watch")
                    df_start_dict = dict(data[0].values.tolist())
                    title = "Test ID: {}, {}, {}".format(df_start_dict['Test:'], df_start_dict['Test Description:'],
                                                         df_start_dict['TestRegime Suffix:'])
                    threading.Thread(target=multiplot,
                                     args=(df_data.iloc[start:stop, :], values['-COL-'], values['-PLOT STYLE-'], True,
                                           values['-PLOT FILE TYPE-'],
                                           values['-GRID-'], (15, 8), work_folder, data[0], window, True,
                                           title,)).start()
                except (NameError, TypeError) as err:
                    Sg.PopupOK("Ingen data vald. \nError: {}".format(err), title="Ingen data")
        elif event == '-ALL-':
            window['-COL-'].set_value(window['-COL-'].get_list_values())
        elif event == '-NONE-':
            window['-COL-'].set_value('[]')
        elif event == '-EXPORT DONE-':
            window.set_cursor("arrow")
            Sg.PopupAutoClose(values['-EXPORT DONE-'], auto_close_duration=3)
        elif event == '-PROCENT-':
            pass
        elif event == '-WORK FOLDER-':
            work_folder = values['-WORK FOLDER-']
        elif event == '-MACCOR TO DF-':
            df_data = values['-MACCOR TO DF-']
            window['-COL-'].Update(values=df_data.columns.tolist())
            data_type = "maccor"
            window.set_cursor("arrow")

        elif event == '-FILE TO DF-':
            # Filen har importerats som Pandas Data Frame
            window.set_cursor("arrow")
            value = values['-FILE TO DF-']
            data = value[0]
            df_data = value[1]
            sections = value[2]
            test_info = value[3]
            if sections['split_results'] != '{}':
                print("Split results: {}".format(sections['split_results']))
            cyclemax = cyclesetmax = df_data['Cycle'].max()
            cyclemin = cyclesetmin = df_data['Cycle'].min()
            print(cyclemin)
            df_data["Power [W]"] = df_data["Voltage [mV]"] * df_data["Current [mA]"] / 1000000
            window['-COL-'].Update(values=df_data.columns.tolist())
            # window['-DESCRIPTION-'].Update(values=data[0].values.tolist())
            window['-DESCRIPTION-'].Update(values=[[key, value] for key, value in test_info.items()])
            window['-CYCLE MAX-'].Update(range=(cyclemin, cyclemax))
            window['-CYCLE MAX-'].Update(value=cyclemax)
            window['-CYCLE MIN-'].Update(range=(cyclemin, cyclemax))
            window['-CYCLE MIN-'].Update(value=cyclemin)
            if len(data) > 1:
                window['-UPDATE DETAILS-'].Update(values=data[-1].values.tolist())
            rows = df_data.shape[0]
            size = round(values['-DATA WINDOW SIZE-'] * rows // 100)
            pos = round(values['-DATA WINDOW POSITION-'] * rows // 100)
            start = (lambda x: 0 if x < 0 else x)(int(pos - size / 2))
            stop = (lambda x: rows if x > rows else x)(int(pos + size / 2))
        elif event == '-FILE TO DF EXCEPTION-':
            window.set_cursor('arrow')
            Sg.PopupError(values['-FILE TO DF EXCEPTION-'])
        elif event == '-SAVE PLOT DONE-':
            window.set_cursor("arrow")
            Sg.PopupAutoClose(values['-SAVE PLOT DONE-'], auto_close_duration=3)
        elif event == '-PLOT DONE-':
            window.set_cursor("arrow")
        elif event == '-CYCLE MIN-':
            cyclesetmin = round(values['-CYCLE MIN-'])
        elif event == '-CYCLE MAX-':
            cyclesetmax = round(values['-CYCLE MAX-'])
            cyclesetmin = round(values['-CYCLE MIN-'])
            window['-CYCLE MIN-'].Update(range=(cyclemin, cyclesetmax))
            if cyclesetmax < cyclesetmin:
                window['-CYCLE MIN-'].Update(value=cyclesetmax)
    window.close()


if __name__ == '__main__':
    main_window()
