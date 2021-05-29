# This script was made to plot data found in CSV-format measurement data files generated by PEC (tm) test equipment
# Written by Henrik Isaksson 2021-05-07
import os

import matplotlib.pyplot as plt
import pandas as pd
import PySimpleGUI as Sg
import time
import re

ignored_columns = ['Test', 'Cell', 'Rack', 'Shelf', 'Position', 'Cell ID', 'Load On time', 'Step Time (Seconds)']
#from tabulate import tabulate

# Pattern of characters allowed in file naming, used with regular expression (re)
name_pattern = '[^a-öA-Ö0-9_]'
global df


# Locate first row of measurement data to be extracted
def find_header(file):
    r_ = 0
    with open(file, 'r') as cf:
        while True:
            r_ += 1
            line = cf.readline()
            if line.startswith("Test,"):
                for x in line.split(','):
                    if x.__contains__('Total Time'):
                        index_ = x
                        break
                return r_, index_


# Read CVS-file into DataFrame df
def file_to_df(_csv_file):
    r, index = find_header(_csv_file)
    df_ = pd.read_csv(_csv_file, skiprows=r - 1, index_col=index, usecols=lambda x: x not in ignored_columns)
    df_.rename(columns=lambda x: re.sub("\(", "[", re.sub("\)", "]", x)), inplace=True)
    return df_


def my_plot(_df, data):
    _df[data].plot()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def plot_to_file(filetype, _df, data, filename):
    _df[data].plot()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(data[0] + "." + filetype, format=filetype)
    plt.close()


def export_data(filetype, _df, data, filename):
    tic = time.process_time()
    if filetype == "excel":
        filename = filename + '.xlsx'
        _df[data].to_excel(filename)
    elif filetype == "text":
        filename = filename + '.txt'
        string_ = _df[data].to_string()
        with open(filename, 'w') as f:
            f.write(string_)
    elif filetype == 'html':
        filename = filename + '.html'
        html = _df[data].to_html()
        with open(filename, 'w') as f:
            f.write(html)
    toc = time.process_time()
    print("Exporten tog: ", (toc - tic), " sekunder")


def main_window():
    global df
    right_column = [[Sg.Text("Datakolumner")], [Sg.Listbox(values=[], size=(55, 20), enable_events=True, k='-COL-',
                                                           select_mode=Sg.LISTBOX_SELECT_MODE_MULTIPLE)],
                    [Sg.Button("Visa plot", key='-SHOW PLOT-'), Sg.Text("Spara plot som:"),
                     Sg.Combo(values=['pdf'], default_value='pdf', readonly=True, enable_events=False,
                              key='-PLOT FILE TYPE-'), Sg.Button("Ok", key='-SAVE PLOT AS-'),
                     Sg.Text("Spara data som:"),
                     Sg.Combo(values=['excel', 'text', 'html'], default_value='excel', enable_events=False,
                              readonly=True, key='-FILE TYPE-'), Sg.Button('Ok', key='-EXPORT FILE-')]]
    main_layout = [[Sg.Text("Open CSV file"), Sg.Input(key='-FILE-', visible=False, enable_events=True),
                    Sg.FileBrowse(file_types=(('ALL Files', '*.csv'),),
                                  initial_folder='/home/henrik/Dokument/Intertek/Mätfiler/SBT8050/')],
                   [Sg.Column(right_column)]]
    window = Sg.Window("Main window", main_layout)
    while True:
        event, values = window.read()
        if event == Sg.WINDOW_CLOSED:
            break
        elif event == "-SHOW PLOT-":
            my_plot(df, values['-COL-'])
        elif event == '-FILE-':
            try:
                file = values['-FILE-']
                t = time.process_time()
                df = file_to_df(file)
                elapsed_time = time.process_time() - t
                print("Processen tog totalt: ", elapsed_time, "s")
                window['-COL-'].Update(values=df.columns.values.tolist())
            except FileNotFoundError:
                Sg.PopupError("Ingen datafil är vald.")
        elif event == '-EXPORT FILE-':
            export_data(values['-FILE TYPE-'], df, values['-COL-'], 'testfil')
        elif event == '-SAVE PLOT AS-':
            # print(df.columns)
            plot_to_file(values['-PLOT FILE TYPE-'], df, values['-COL-'], values['-COL-'])

    window.close()


main_window()
plt.show()
