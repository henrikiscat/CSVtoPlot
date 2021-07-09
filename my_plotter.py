import matplotlib.pyplot as plt
import re


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


def multiplot(_df, data, style_, save, filetype, grid_on, figsize_, work_folder, df_start, window, interpolate):
    plt.close()
    if interpolate:
        _df = _df.interpolate()
    units = list(map(unit_list, data))  # List of data units
    slice_list = slice_it(units)  # Data slices with two units each
    total_nu = count_units(units)  # Total number of unique units in data
    plot_left_adjust = 0.1
    plot_right_adjust = 0.90
    df_start_dict = dict(df_start.values.tolist())
    title = "Test ID: {}, {}, {}".format(df_start_dict['Test:'], df_start_dict['Test Description:'],
                                         df_start_dict['TestRegime Suffix:'])
    if total_nu <= 2:
        if total_nu == 2:
            left_unit = re.sub(']', '', data[0].split('[')[-1])
            right_unit = re.sub(']', '', data[-1].split('[')[-1])
            right_data = [x for x in data if left_unit not in x]
            ax = _df[data].plot(figsize=figsize_, secondary_y=right_data, legend=False, style=style_)
            ax.set_ylabel(left_unit)
            lines1, labels1 = ax.get_legend_handles_labels()
            if hasattr(ax, 'right_ax'):
                ax.right_ax.set_ylabel(right_unit)
                lines2, labels2 = ax.right_ax.get_legend_handles_labels()
                labels2 = [x + ' (right)' for x in labels2]
                ax.right_ax.legend(lines1 + lines2, labels1 + labels2)
                ax.right_ax.grid(grid_on)
                print(labels1)
            else:
                ax.legend(lines1, labels1)
            ax.grid(grid_on)
        else:
            _df[data].plot(figsize=figsize_, style=style_)
            plt.legend()
            plt.grid(grid_on)
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
            _df[data[slice_list[j]]].plot(ax=ax_, secondary_y=right_data, legend=False, sharex=False)
            lines1, labels1 = ax_.get_legend_handles_labels()
            if hasattr(ax_, 'right_ax'):
                lines2, labels2 = ax_.right_ax.get_legend_handles_labels()
                labels2 = [x + ' (right)' for x in labels2]
                ax_.right_ax.set_ylabel(right_unit)
                ax_.right_ax.legend(lines1 + lines2, labels1 + labels2)
                ax_.right_ax.grid(grid_on)
            else:
                lines, labels = ax_.get_legend_handles_labels()
                ax_.legend(lines, labels)
            ax_.grid(grid_on)
            ax_.set_ylabel(left_unit)
    if save:
        file_name = "{}/{}_{}.{}".format(work_folder, df_start_dict['Test:'], data[0].split('[')[0], filetype)
        plt.savefig(file_name,
                    format=filetype)
        window.write_event_value('-SAVE PLOT DONE-', "Plotten sparades som: {}".format(file_name))
    else:
        window.write_event_value('-PLOT DONE-', '')

        plt.show()

