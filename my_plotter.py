import matplotlib.pyplot as plt
from matplotlib import rcParams
from cycler import cycler
import re
import matplotlib.colors as matcol
from pandas.plotting import table
import matplotlib.transforms as transf
import numpy as np
import matplotlib.ticker as tick


def tint_hex(col_rgb, tint):
    rgb_tint = tuple((x + (255 - x)*tint)/255 for x in col_rgb)
    return matcol.to_hex(rgb_tint)


plt.close()
# black '#ffc700',
#colors = ['#130c0e', '#21b6d7', tint_hex((33, 182, 215), 0.25), tint_hex((33, 182, 215), 0.5), '#474e54',
 #         tint_hex((71, 78, 84), 0.25), tint_hex((71, 78, 84), 0.5)]

#
colors = 'bgrcmyk'

color_dict = {'V': 'blue', 'mV': 'blue', 'A': 'red', 'mA': 'red', 'Ah': 'g', 'mAh': 'g', 'Wh': 'darkorange',
              'mWh': 'darkorange', '\u00B0C': 'lightseagreen'}

rc_annotate = ['Front CAN bus Off error', 'Internal CAN bus Off error', 'TempMax', 'TempMin']

cycler_ = (cycler(color=colors))
rcParams['font.sans-serif'] = ['Calibri', 'Neo Sans']
nticks = None
#plt.rc('axes', prop_cycle=cycler_, )


def slice_it(units):
    slice_list = []
    nu = 1
    beg = 0
    u = units[0]
    for i in range(len(units)):
        unit = units[i]
        if unit != u:
            u = unit
            nu += 1
            if nu == 3:
                print("Three units detected, current unit: {}".format(unit))
                slice_list.append(slice(beg, i))
                beg = i
                nu = 1
    if beg <= (len(units) - 1):
        slice_list.append(slice(beg, len(units)))
    return slice_list


def unit_list(x):
    if "[" in x:
        result = x.split("[")[1].split("]")[0]
    else:
        result = "Na"
    return result


def count_units(units):
    unit = units[0]
    n = 1
    for x in units[1:]:
        if x != unit:
            n += 1
            unit = x
    return n


def annotate_(df, ax, annotate):
    for i in annotate:
        data = df[df['ReasonCode Name'] == i]
        for row_index, row in data['Voltage [mV]'].items():
            print("Row index: {}, value: {}, RC: {}".format(row_index, row, i))
            ax.annotate(i, xy=(row_index, ax.get_ybound()[0] + 2), xytext=(10, -3), textcoords='offset points')
            #(row_index, row)
            #data['Voltage [mV]']
        ax.scatter(data.index, [ax.get_ybound()[0] - (ax.get_ybound()[1] - ax.get_ybound()[0])*0.01]*len(data.index))


def extra_tics(df, ax, rc_):
    ex_ticks = []
    rc = df['ReasonCode Name'].values.tolist()
    print([x if x in rc else [] for x in rc_])
    for i in rc_:
        if i in rc:
            print(i)
            data = df[df['ReasonCode Name'] == i]
            ex_ticks += data.index.values.tolist()
    print("ex_ticks: {}".format(ex_ticks))
        #for row_index, row in data['Voltage [mV]'].items():
    #extra_tics += [x for x, y in data['Voltage [mV]'].items()]
    #ax.set_xticks(df.index.values.tolist() + extra_tics)


def info_table(data_, ax_):
    table(ax=ax_, data=data_, loc='right', colWidths=[.2, .2], bbox=(1.27, 0, .19, 1))
    plt.subplots_adjust(right=.7)


def format_time(index, time_format):
    if time_format == 'h':
        return index//(3600*1000)
    elif time_format == 's':
        return index//1000
    elif time_format == 'datetime':
        return index.to_timedelta(index, unit='ms')


def multiplot(_df, data, style_, save, filetype, grid_on, figsize_, work_folder, df_start, window, interpolate, title,
               test_info, axs_margin, time_format, grid_on_both_axis):
    if interpolate:
        _df = _df.interpolate()
    if time_format:
        #print(format_time(_df.index, time_format))
        _df.index = format_time(_df.index, time_format)
        _df.index.name = f'{_df.index.name} [{time_format}]'
    units = list(map(unit_list, data))  # List of data units
    slice_list = slice_it(units)  # Data slices with two units each
    total_nu = count_units(units)  # Total number of unique units in data
    plot_left_adjust = .1
    plot_right_adjust = .9
    global nticks
    if total_nu <= 2:
        if total_nu == 2:
            left_unit = re.sub(']', '', data[0].split('[')[-1])
            right_unit = re.sub(']', '', data[-1].split('[')[-1])
            right_data = [x for x in data if left_unit not in x]
            ax = _df[data].plot(figsize=figsize_, secondary_y=right_data, legend=False, style=style_,
                                color=[color_dict.get(x, 'cornflowerblue') for x in [left_unit, right_unit]])
            ax.set_ylabel(left_unit)
            lines1, labels1 = ax.get_legend_handles_labels()
            if hasattr(ax, 'right_ax'):
                ax.right_ax.set_ylabel(right_unit)
                lines2, labels2 = ax.right_ax.get_legend_handles_labels()
                labels2 = [x + ' (right)' for x in labels2]
                ax.right_ax.legend(lines1 + lines2, labels1 + labels2)
                ax.right_ax.set_ymargin(axs_margin)
                if grid_on:
                    if grid_on_both_axis:
                        ax.yaxis.set_major_locator(tick.LinearLocator(nticks))
                        ax.right_ax.yaxis.set_major_locator(tick.LinearLocator(nticks))
                    else:
                        ax.grid(grid_on)
            else:
                ax.legend(lines1, labels1)
            ax.grid(grid_on)
            ax.set_ymargin(axs_margin)

        else:
            unit = re.sub(']', '', data[0].split('[')[-1])
            ax = _df[data].plot(figsize=figsize_, style=style_, ylabel=unit, color=color_dict.get(unit, 'cornflowerblue'))
            ax.grid(grid_on)
            ax.set_ymargin(axs_margin)
        plt.title(title)
    else:
        fig, axs = plt.subplots(nrows=((total_nu // 2) + (1 if (total_nu % 2) != 0 else 0)), ncols=1, figsize=figsize_,
                                sharex=False)
        plt.subplots_adjust(left=plot_left_adjust, right=plot_right_adjust)
        axs[0].set_title(title)
        for j in range(len(axs)):
            ax_ = axs[j]
            data_slice = data[slice_list[j]]
            left_unit = re.sub(']', '', data_slice[0].split('[')[-1])
            right_unit = re.sub(']', '', data_slice[-1].split('[')[-1])
            right_data = [x for x in data_slice if left_unit not in x]
            _df[data[slice_list[j]]].plot(ax=ax_, color=[color_dict.get(x, 'darksalmon') for x in [left_unit,
                                                                                                       right_unit]],
                                          secondary_y=right_data, legend=False, sharex=True)
            lines1, labels1 = ax_.get_legend_handles_labels()
            if hasattr(ax_, 'right_ax'):
                lines2, labels2 = ax_.right_ax.get_legend_handles_labels()
                labels2 = [x + ' (right)' for x in labels2]
                ax_.right_ax.set_ylabel(right_unit)
                ax_.right_ax.legend(lines1 + lines2, labels1 + labels2)
                if grid_on:
                    if grid_on_both_axis:
                        ax_.yaxis.set_major_locator(tick.LinearLocator(nticks))
                        ax_.right_ax.yaxis.set_major_locator(tick.LinearLocator(nticks))
                ax_.grid(grid_on)
            else:
                lines, labels = ax_.get_legend_handles_labels()
                ax_.legend(lines, labels)
                ax_.grid(grid_on)
            ax_.set_ylabel(left_unit)

    if save:
        file_name = "{}/{}_{}.{}".format(work_folder, dict(df_start.values.tolist())['Test:'], data[0].split('[')[0],
                                         filetype)
        plt.savefig(file_name,
                    format=filetype)
        plt.close()
        window.write_event_value('-SAVE PLOT DONE-', "Plotten sparades som: {}".format(file_name))
    else:
        window.write_event_value('-PLOT DONE-', '')
        plt.show()
        plt.close()

