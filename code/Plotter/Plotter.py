"""Get avg computed by receiver from LSL and plot them."""

import os
import signal
import sys
import time
import tkinter
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pylsl.pylsl
from matplotlib import gridspec
from pylsl import StreamInlet, resolve_stream

# Constants ----------------------------------------------------------------------------------------------------------------------
OUTPUT_PATH = os.path.join("..", "..", "output", "Plots")  # folder location for saving plots
OUTPUT_FILE = 'channels_avg_' + time.strftime("%Y_%b_%d_%H%M") + '.png'  # file name
# plots values
MAX_COLS = 4
MAX_ROWS = 8

# Flags and variables for optional features --------------------------------------------------------------------------------------
USING_CONSOLE = True    # flag to enable the console control

DEBUG_PRINT = False     # flag to enable verbose prints

if USING_CONSOLE:
    CONSOLE_PATH = os.path.join("..", "Console")
    sys.path.insert(0, CONSOLE_PATH)
    from Console import DEBUG_PRINT  # overwrite the value of DEBUG_PRINT flag with the one inside Console file


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):  # define format of warning prints
    return '%s: %s\n' % (category.__name__, message)


def y_lim(f_segment_avg, r_segment_avg, diff):  # return global min and max values of y axes for all subplots
    f_min = np.amin(f_segment_avg)
    r_min = np.amin(r_segment_avg)
    d_min = np.amin(diff)
    f_max = np.amax(f_segment_avg)
    r_max = np.amax(r_segment_avg)
    d_max = np.amax(diff)
    return np.amin(np.array([f_min, r_min, d_min])), np.amax(np.array([f_max, r_max, d_max]))


def channels_plot(fig, axs, time_steps, f_segment_avg, r_segment_avg, event_init, s_type, rare_line, freq_line, diff_line):
    diff = r_segment_avg - f_segment_avg
    y_min, y_max = y_lim(f_segment_avg, r_segment_avg, diff)
    for i in range(len(axs)):  # for each subplot
        if s_type == 1:  # rare event
            rare_line[i].remove()
            rare_line[i], = axs[i].plot(time_steps, r_segment_avg[:, i], color=(0.42, 0.68, 0.84, 1))
        else:  # frequent event
            freq_line[i].remove()
            freq_line[i], = axs[i].plot(time_steps, f_segment_avg[:, i], color=(0.98, 0.42, 0.29, 1))
        diff_line[i].remove()
        diff_line[i], = axs[i].plot(time_steps, diff[:, i], color='k')
        axs[i].set_ylim(y_min - 0.15 * abs(y_min), y_max + 0.15 * abs(y_max))  # update ylim
    fig.suptitle("Last event at time: " + str(event_init), horizontalalignment='center', fontsize=10)
    fig.canvas.draw()
    fig.canvas.flush_events()  # needed to immediately update plot
    plt.pause(0.001)
    return rare_line, freq_line, diff_line


def reset_plot(fig, axs, time_steps, f_segment_avg, r_segment_avg, event_init, rare_line, freq_line, diff_line):
    diff = r_segment_avg - f_segment_avg
    y_min, y_max = y_lim(f_segment_avg, r_segment_avg, diff)
    for i in range(len(axs)):  # for each subplot
        rare_line[i].remove()
        freq_line[i].remove()
        diff_line[i].remove()
        rare_line[i], = axs[i].plot(time_steps, r_segment_avg[:, i], color=(0.42, 0.68, 0.84, 1))
        freq_line[i], = axs[i].plot(time_steps, f_segment_avg[:, i], color=(0.98, 0.42, 0.29, 1))
        diff_line[i], = axs[i].plot(time_steps, diff[:, i], color='k')
        if not y_min == y_max == 0:
            axs[i].set_ylim(y_min - 0.15 * abs(y_min), y_max + 0.15 * abs(y_max))  # update ylim
    fig.suptitle("Avgs reset at time: " + str(event_init), horizontalalignment='center', fontsize=10)
    fig.canvas.draw()
    fig.canvas.flush_events()  # needed to immediately update plot
    plt.pause(0.001)
    return rare_line, freq_line, diff_line


def main():
    # Get data from LSL ----------------------------------------------------------------------------------------------------------
    # first resolve the avg stream on the lsl network
    print("Looking for the avg stream...", end=" ")
    avg_streams = resolve_stream('name', 'avgStream')
    # create a new inlet to read from the stream
    avg_inlet = StreamInlet(avg_streams[0], recover=False)
    print("done!")

    # get stream info
    info = avg_inlet.info()
    n_channels = info.channel_count()
    dequeues_len = int(info.desc().child("chunk").child_value("size"))

    ch = info.desc().child("channels").child("channel")
    labels = []
    for i in range(n_channels):
        labels.append(ch.child_value("label"))
        ch = ch.next_sibling()

    x_info = info.desc().child("x_info")
    pause_pre_ev = float(x_info.child_value("pause_pre_ev"))
    event_length = float(x_info.child_value("event_length"))
    pause_post_ev = float(x_info.child_value("pause_post_ev"))
    EEG_srate = float(x_info.child_value("EEG_srate"))
    time_steps = np.arange(-pause_pre_ev, event_length + pause_post_ev, 1 / EEG_srate)  # list containing steps, used in plot

    # Initialization -------------------------------------------------------------------------------------------------------------
    f_segment_avg = np.zeros((dequeues_len, n_channels))
    r_segment_avg = np.zeros((dequeues_len, n_channels))
    chunk = np.zeros((dequeues_len, n_channels))
    event_init = 0
    s_type = 0

    plotting = False  # used to know if execution interrupted while updating plots
    plt.ion()  # to plot always on same window

    # window sizing warning
    n_col = int(np.ceil(n_channels / MAX_ROWS))
    n_row = int(np.ceil(n_channels / n_col))
    if n_channels > MAX_ROWS * MAX_COLS:
        warnings.formatwarning = warning_on_one_line
        warnings.warn("the detected EEG stream has more than {} channels, thus the window of the plots may be not correctly sized."
                      "\nPlease adjust the size of windows before continuing, and consider to increase the values of MAX_ROWS "
                      "and/or MAX_COLS macros in the code for the future executions, if the current experiment would be repeated."
                      "\nThe current values have been chosen as a compromise between quantity and quality of the plots, so we do "
                      "not guarantee the visual quality of the results once the original values have been modified.\nhint: It is"
                      " advisable to prefer to increase the number of rows rather than columns!".format(MAX_COLS * MAX_ROWS))

    # get monitor info to set figure's window correctly
    root = tkinter.Tk()
    my_dpi = root.winfo_fpixels('1i')
    root.withdraw()
    monitor_w, monitor_h = root.winfo_screenwidth(), root.winfo_screenheight()
    fig = plt.figure(constrained_layout=True,
                     figsize=((monitor_w / my_dpi) * n_col / MAX_COLS, ((0.97 * monitor_h) / my_dpi) * n_row / MAX_ROWS),
                     dpi=my_dpi)
    fig.set_constrained_layout_pads(w_pad=0.1, h_pad=0.1)  # add some margin
    fig.canvas.manager.set_window_title('Channels averaging')

    # create subplots structure (according to n_channels)
    spec = gridspec.GridSpec(ncols=n_col, nrows=n_row, figure=fig)
    rare_line = [0 for _ in range(n_channels)]
    freq_line = [0 for _ in range(n_channels)]
    diff_line = [0 for _ in range(n_channels)]
    axs = []
    for i in range(n_channels):
        row = i % n_row
        col = int(i / n_row)
        ax = fig.add_subplot(spec[row, col])
        rare_line[i], = ax.plot(time_steps, r_segment_avg[:, i], color=(0.42, 0.68, 0.84, 1))
        freq_line[i], = ax.plot(time_steps, f_segment_avg[:, i], color=(0.98, 0.42, 0.29, 1))
        diff_line[i], = ax.plot(time_steps, r_segment_avg[:, i] - f_segment_avg[:, i], color='k')
        ax.plot(time_steps, r_segment_avg[:, i] - f_segment_avg[:, i], ':', color='grey')  # dashed line at y==0
        ax.set(ylabel=labels[i] + " [$\mu$V]")  # put channel label
        if (i % n_row) != (n_row - 1) and i != (n_channels - 1):
            ax.tick_params(axis='x', label1On=False)  # want to show x_ticks only in last row of grid
        else:
            ax.set(xlabel="Time [s]")
        axs.append(ax)
    line_labels = ["Rare event", "Frequent event", "Difference"]
    fig.legend(labels=line_labels, loc='upper right', borderaxespad=0.1, prop={'size': 8})
    fig.suptitle("\n", horizontalalignment='center', fontsize=5)  # just to leave same space occupied later by real title
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.1)

    # define handler for whenever the application is interrupted (e.g. with ctrl+c), to save current plots
    def sigint_handler():
        sys.stdout.write("\n")
        print('Application interrupted!')
        print("Saving obtained plots in 'output' folder...", end=" ")
        if plotting:  # i.e. code interrupted while updating plots
            print("(finishing the plot latest event, occurred at " + str(event_init) + "s, from where interrupted...", end=" ")
            channels_plot(fig, axs, time_steps, f_segment_avg, r_segment_avg,
                          event_init, s_type, rare_line, freq_line, diff_line)  # to make sure to have it updated!
            print("done!)", end=" ")
        if not os.path.exists(OUTPUT_PATH):
            os.makedirs(OUTPUT_PATH)
        plt.savefig(os.path.join(OUTPUT_PATH, OUTPUT_FILE))
        print("done!")
        sys.exit()

    signal.signal(signal.SIGINT, sigint_handler)  # register the signal handler

    # Setup console --------------------------------------------------------------------------------------------------------------
    if USING_CONSOLE:
        ''' Continuously sends to the Console a key message ("OK"), to 
        confirm that this process is ready to begin the acquisition
        and wait for a key message ("NEXT") from the Console that will
        arrive when all the interested processes are ready '''
        info_console = pylsl.StreamInfo('Plotter', 'Text', 1, 0, 'string')
        outlet_console = pylsl.StreamOutlet(info_console)

        console_streams = resolve_stream('name', 'Console')
        console_inlet = StreamInlet(console_streams[0], recover=False)

        print("Ready to receive and plot data!")

        while True:
            try:
                msg, timestamp = console_inlet.pull_sample(timeout=1)
                outlet_console.push_sample(['OK'])
                if msg is not None and msg[0] == 'NEXT':
                    break
            except ():
                sys.stdout.write("\n")
                sys.exit()

    else:
        print("Ready to receive and plot data!")

    # Read data ------------------------------------------------------------------------------------------------------------------
    while True:
        try:
            # get new chunk
            for i in range(dequeues_len):
                chunk[i], event_init = avg_inlet.pull_sample()  # blocking call
                if (chunk[i] == 0).sum() == chunk[i].size and event_init != 0.00001:  # all elements are 0 == closing condition
                    s_type = -1  # flag to close everything
                    break  # exit the for cycle
            if s_type == -1:
                break  # exit the while cycle
            if USING_CONSOLE and event_init == 0.00001:  # in case of a discard/restart (stop + play) command
                r_segment_avg[:] = chunk
                for i in range(dequeues_len):  # pull new chunk
                    chunk[i], event_init = avg_inlet.pull_sample()  # blocking call
                f_segment_avg[:] = chunk
                if event_init == 0.00001:  # restart (stop + play) case
                    print("Resetting to start from scratch...", end="")
                    event_init = 0.0
                    print("done!")
                else:
                    event_init = round(event_init, 4)
                plotting = True
                rare_line, freq_line, diff_line = reset_plot(fig, axs, time_steps, f_segment_avg, r_segment_avg,
                                                             event_init, rare_line, freq_line, diff_line)
                plotting = False
                if DEBUG_PRINT:
                    print("Avgs reset at " + str(event_init) + "s")
                    print("===========================================================")
                continue  # goes to next iteration
            if f_segment_avg[0][0] - r_segment_avg[0][0] == 0:  # i.e. first time printed something in this cycle (or after restart)
                print("Receiving data...")
            if DEBUG_PRINT:
                if f_segment_avg[0][0] - r_segment_avg[0][0] == 0:
                    print("")
                print("Avg data: ")
                print("\ttimestamp: " + str(round(event_init, 4)))
                print("\tchunk: " + str(chunk))
                print("----------------------------------------")
            if event_init < 0:  # rare event
                s_type = 1
                event_init = abs(round(event_init, 4))  # recover real timestamp
                r_segment_avg[:] = chunk
            elif event_init > 0:  # frequent event
                s_type = 0
                event_init = round(event_init, 4)
                f_segment_avg[:] = chunk
            if DEBUG_PRINT:
                print("\ttimestamp: " + str(event_init))
                print("\ts_type: " + str(s_type))
                print("===========================================================")

            plotting = True
            rare_line, freq_line, diff_line = channels_plot(fig, axs, time_steps, f_segment_avg, r_segment_avg,
                                                            event_init, s_type, rare_line, freq_line, diff_line)
            plotting = False

            if DEBUG_PRINT:
                if s_type == 1:  # rare event
                    print("Plotted rare event occurred at " + str(event_init) + "s")
                else:  # frequent event
                    print("Plotted frequent event occurred at " + str(event_init) + "s")
                print("===========================================================")

        except (pylsl.pylsl.LostError, pylsl.pylsl.TimeoutError):  # i.e. if connection lost
            sys.stdout.write("\n")
            print("Connection lost with the receiver!")
            print("Closing streams...", end=" ")
            avg_inlet.close_stream()
            if USING_CONSOLE:
                console_inlet.close_stream()
            print("done!")
            if not os.path.exists(OUTPUT_PATH):
                os.makedirs(OUTPUT_PATH)
            plt.savefig(os.path.join(OUTPUT_PATH, OUTPUT_FILE))
            print("Saving obtained plots in 'output' folder... done!")
            sys.exit()

    sys.stdout.write("\n")
    print('Session ended!')
    print("Closing streams...", end=" ")
    avg_inlet.close_stream()
    print("done!")
    print("Saving obtained plots in 'output' folder...", end=" ")
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    plt.savefig(os.path.join(OUTPUT_PATH, OUTPUT_FILE))
    print("done!")
    if USING_CONSOLE:
        # send msg to console
        while True:
            outlet_console.push_sample(['DONE'])
            msg, timestamp = console_inlet.pull_sample(timeout=0)
            if msg is not None and msg[0] == 'CLOSE_ALL':
                break


if __name__ == '__main__':
    main()
