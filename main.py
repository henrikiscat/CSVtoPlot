# This script was made to plot data found in CSV-format measurement data files generated by PEC (tm) test equipment
# Written by Henrik Isaksson 2021-05-07
import os

import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
import PySimpleGUI as Sg
import re
import time
import numpy as np

name_pattern = '[^a-öA-Ö0-9_]'


#custom_time_parser = lambda x: datetime.strptime(x, "%H:%M:%S.%f")


def file_chooser():
    layout = [[Sg.Text('Chose file to import')], [Sg.Input(key="-FILE-", visible=False, enable_events=True), Sg.FileBrowse()]]
    event, values = Sg.Window('File chooser', layout).read(close=True)
    return values['-FILE-']


# Find first row of data
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


# Time the procedure
t = time.process_time()


# Read CVS-file into DataFrame df
def file_to_df(_csv_file):
    r, index = find_header(_csv_file)
    return pd.read_csv(_csv_file, skiprows=r-1, index_col=index)



def my_plot(_df, data):
    _df[data].plot()
    plt.show()


def main_window():

    left_column = [
                   [Sg.Text('Filer')], [Sg.Listbox(values=[], enable_events=False, size=(25, 20), key='-FILE LIST-')],
                   [Sg.Button("Läs in", key="-READ FILE-")]]
    right_column = [[Sg.Text("Data")], [Sg.Listbox(values=[], size=(25, 20), enable_events=True, k='-COL-',
                                                  select_mode=Sg.LISTBOX_SELECT_MODE_MULTIPLE)],
                    [Sg.Button("Visa plot", key='-SHOW PLOT-'), Sg.Button("Spara plot som PDF", key='-SAVE PLOT AS PDF')]]
    main_layout = [[Sg.Text("Folder"), Sg.In(size=(25, 1), enable_events=True, key='-FOLDER-'), Sg.FolderBrowse()],
                   [Sg.Column(left_column), Sg.Column(right_column)]]
    window = Sg.Window("Main window", main_layout)
    while True:
        event, values = window.read()
        if event == Sg.WINDOW_CLOSED:
            break
        elif event == "-SHOW PLOT-":
            my_plot(df, values['-COL-'])
        elif event == '-FOLDER-':
            folder = values['-FOLDER-']
            try:
                file_list = os.listdir(folder)
            except:
                file_list = []
            fnames = [f for f in file_list if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith('.csv')]
            window['-FILE LIST-'].Update(values=fnames)
        elif event == '-READ FILE-':
            file = os.path.join(values['-FOLDER-'], values['-FILE LIST-'][0])
            print(file)
            df = file_to_df(file)
            window['-COL-'].Update(values=df.columns.values.tolist())

    window.close()

main_window()


print(df.info())
#df.plot('Current (mA)')
#plt.show()
#my_plot(df['Current (mA)'])
elapsed_time = time.process_time() - t
print("Processen tog totalt: ", elapsed_time, "s")
plt.show()

