"""Read a multi-channel time series with proper meta-data from LSL in single samples and compute averaged potential"""
import csv
import getopt
import os
import signal
import sys
import time
from collections import deque
from time import sleep

import numpy as np
import pylsl.pylsl
from pylsl import StreamInlet, resolve_stream, StreamInfo, StreamOutlet
from scipy import signal as dsp

# Constants -------------------------------------------------------------------------------------------------------------------------
DATE_STR = time.strftime("%Y_%b_%d_%H%M")
OUTPUT_PATH = os.path.join("..", "..", "output", "Recordings", "rec_session_" + DATE_STR)  # folder location for saving csv
OUTPUT_FILE_EEG = 'eeg_session_' + DATE_STR + '.csv'    # EEG dataset
OUTPUT_FILE_EVS = 'evs_session_' + DATE_STR + '.csv'    # events dataset
OUTPUT_FILE_DISC = 'disc_session_' + DATE_STR + '.csv'  # discard dataset

# filter values (band-pass)
FRI_NUMTAPS = 1000
LOWER_COF = 1   # lower cutoff frequency
UPPER_COF = 24  # upper cutoff frequency

# filter values (notch filter)
SAMP_FREQ = 1000  # sample frequency (Hz)
NOTCH_FREQ = 50.0  # frequency to be removed from signal (Hz)
QUALITY_FACTOR = 30.0  # quality factor

# values defining size of window used to calculate aligned averaged potentials
PAUSE_PRE_EV = 0.0      # s, baseline duration
EVENT_LENGTH = 0.5      # s, stimulus duration
PAUSE_POST_EV = 0.3     # s, post-stimulus duration

# Flags and variables for optional features -----------------------------------------------------------------------------------------
SELECTED_CHANNELS = False   # flag to compute and plot the averaged potentials of a subset of channels
selected_channels = ['Cz']

RECORDING = True            # flag to save datasets of the experiments

USING_CONSOLE = True        # flag to enable the console control

DEBUG_PRINT = False         # flag to enable verbose prints

if USING_CONSOLE:
    CONSOLE_PATH = os.path.join("..", "Console")
    sys.path.insert(0, CONSOLE_PATH)
    from Console import DEBUG_PRINT  # overwrite the value of DEBUG_PRINT flag with the one inside Console file


def avg(data_segment, segment_avg, n_event):  # computes cumulative moving average
    segment_avg = (data_segment + (n_event * segment_avg)) / (n_event + 1)
    n_event += 1
    return segment_avg, n_event


def main(argv):
    pause_pre_ev = PAUSE_PRE_EV
    event_length = EVENT_LENGTH
    pause_post_ev = PAUSE_POST_EV

    # get values from arguments of main if these are given
    help_string = 'Receiver.py -b <pause_pre_ev> -e <event_length> -p <pause_post_ev>'
    try:
        opts, args = getopt.getopt(argv, "hb:e:p:", longopts=["pause_pre_ev=", "event_length=", "pause_post_ev"])
    except getopt.GetoptError:
        print(help_string)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(help_string)
            sys.exit()
        elif opt in ("-b", "--pause_pre_ev"):
            pause_pre_ev = float(arg)
        elif opt in ("-e", "--event_length"):
            event_length = float(arg)
        elif opt in ("-p", "--pause_post_ev"):
            pause_post_ev = float(arg)

    # EEG data ----------------------------------------------------------------------------------------------------------------------
    # first resolve an EEG stream on the lsl network
    print("Looking for the EEG stream...", end=" ")
    data_streams = resolve_stream('type', 'EEG')
    # create a new inlet to read from the stream
    data_inlet = StreamInlet(data_streams[0], recover=False)
    print("done!")

    # get stream info
    info = data_inlet.info()
    srate = info.nominal_srate()  # Hz
    n_channels = info.channel_count()
    ch = info.desc().child("channels").child("channel")
    labels = []
    labels_ids = []
    for i in range(n_channels):
        if not SELECTED_CHANNELS:
            labels.append(ch.child_value("label"))
        else:
            if ch.child_value("label") in selected_channels:
                labels.append(ch.child_value("label"))
                labels_ids.append(i)
        ch = ch.next_sibling()
    n_channels = len(labels)

    # compute length of segments from values of srate, pause_pre_ev, pause_post_ev and event_length
    samples_pre_ev = int(np.ceil(pause_pre_ev * srate))
    samples_post_ev = int(np.ceil(pause_post_ev * srate))
    event_samples = int(np.ceil(event_length * srate))
    dequeues_len = samples_pre_ev + samples_post_ev + event_samples

    # create dequeues fot EEG data and timestamps
    data_segment = deque([0 for _ in range(dequeues_len)])
    time_segment = deque([0 for _ in range(dequeues_len)])

    # initialization for avg
    f_events = []       # list containing timestamp of frequent events occurred but yet not considered
    r_events = []       # list containing timestamp of rare events occurred but yet not considered
    n_freq_event = 0
    n_rare_event = 0
    f_segment_avg = np.zeros((dequeues_len, n_channels))
    r_segment_avg = np.zeros((dequeues_len, n_channels))
    if USING_CONSOLE:
        f_segment_avg_10s = np.zeros((dequeues_len, n_channels))
        r_segment_avg_10s = np.zeros((dequeues_len, n_channels))
        # dict containing averages computed in last 10 s, together with the number of frequent and rare events averaged at that time
        dict_avg_10s = {-1: [f_segment_avg_10s, r_segment_avg_10s, n_freq_event, n_rare_event],
                        0: [f_segment_avg_10s, r_segment_avg_10s, n_freq_event, n_rare_event]}

    # needed computations for filters
    avg_padded = np.zeros(((2 * int(srate)) + dequeues_len))  # add 1s before and after segment, to avoid filter distortion
    fir = dsp.firwin(FRI_NUMTAPS, [LOWER_COF, UPPER_COF], pass_zero=False, fs=srate)    # for band-pass filter
    b_notch, a_notch = dsp.iirnotch(NOTCH_FREQ, QUALITY_FACTOR, SAMP_FREQ)              # for notch filter

    if RECORDING:
        # initialize csv file
        if not os.path.exists(OUTPUT_PATH):
            os.makedirs(OUTPUT_PATH)
        log_eeg = open(os.path.join(OUTPUT_PATH, OUTPUT_FILE_EEG), 'w', newline='')
        log_evs = open(os.path.join(OUTPUT_PATH, OUTPUT_FILE_EVS), 'w', newline='')
        log_disc = open(os.path.join(OUTPUT_PATH, OUTPUT_FILE_DISC), 'w', newline='')
        # create the csv writers
        eeg_writer = csv.writer(log_eeg)
        evs_writer = csv.writer(log_evs)
        disc_writer = csv.writer(log_disc)

    # Plot data ---------------------------------------------------------------------------------------------------------------------
    # first create a new stream info. The last value would be a more or less locally
    # unique identifier for the stream as far as available (you could also omit
    # it but interrupted connections wouldn't auto-recover).
    # info = StreamInfo(name, type, n_channels, srate, channels_format, id)
    avg_info = StreamInfo('avgStream', 'avg', n_channels, 0, 'float32', 'myuid2425')

    # append some meta-data
    chunk_info = avg_info.desc().append_child("chunk")
    chunk_info.append_child_value("size", str(dequeues_len))

    chns = avg_info.desc().append_child("channels")
    for label in labels:
        ch = chns.append_child("channel")
        ch.append_child_value("label", label)

    x_info = avg_info.desc().append_child("x_info")
    x_info.append_child_value("pause_pre_ev", str(pause_pre_ev))
    x_info.append_child_value("event_length", str(event_length))
    x_info.append_child_value("pause_post_ev", str(pause_post_ev))
    x_info.append_child_value("EEG_srate", str(srate))

    # next make an outlet, with chunk size = dequeues_len
    avg_outlet = StreamOutlet(avg_info, dequeues_len)

    # define handler for whenever the application is interrupted (e.g. with ctrl+c)
    def sigint_handler():
        sys.stdout.write("\n")
        print('Application interrupted!')
        if RECORDING:
            print("Closing csv file...", end=" ")
            log_eeg.close()
            log_evs.close()
            log_disc.close()
            print("done!")
        sys.exit()

    signal.signal(signal.SIGINT, sigint_handler)  # register the signal handler

    sleep(0.1)  # OBS: added to avoid mixing of prints
    # Marker data -------------------------------------------------------------------------------------------------------------------
    print("Looking for markers' stream...", end=" ")
    marker_streams = resolve_stream('name', 'MarkerStream')
    # create a new inlet to read from the stream
    marker_inlet = StreamInlet(marker_streams[0], recover=False)
    print("done!")

    # Setup console -----------------------------------------------------------------------------------------------------------------
    if USING_CONSOLE:
        ''' Continuously sends to the Console a key message ("OK"), to 
        confirm that this process is ready to begin the acquisition
        and wait for a key message ("NEXT") from the Console that will
        arrive when all the interested processes are ready '''
        info_console = pylsl.StreamInfo('Receiver', 'Text', 1, 0, 'string')
        outlet_console = pylsl.StreamOutlet(info_console)

        console_streams = resolve_stream('name', 'Console')
        console_inlet = StreamInlet(console_streams[0], recover=False)

        print("Ready to receive data!")

        while True:
            try:
                outlet_console.push_sample(['OK'])
                msg, timestamp = console_inlet.pull_sample(timeout=0)
                if msg is not None and msg[0] == 'NEXT':
                    break
            except (pylsl.pylsl.LostError, pylsl.pylsl.TimeoutError):
                sys.stdout.write("\n")
                sys.exit()

    else:
        print("Ready to receive data!")

    # Read data ---------------------------------------------------------------------------------------------------------------------
    while True:
        try:
            # get new EEG and marker sample
            sample, data_time = data_inlet.pull_sample()  # blocking call
            marker, marker_time = marker_inlet.pull_sample(timeout=0)
            if USING_CONSOLE and data_time == 0.00001:  # restart (stop + play msgs) case
                if not DEBUG_PRINT:
                    print("")
                print("Resetting to start from scratch...", end="")
                # reinitialized everything
                # variables initialization
                data_segment = deque([0 for _ in range(dequeues_len)])
                time_segment = deque([0 for _ in range(dequeues_len)])
                f_events = []
                r_events = []
                n_freq_event = 0
                n_rare_event = 0
                f_segment_avg = np.zeros((dequeues_len, n_channels))
                r_segment_avg = np.zeros((dequeues_len, n_channels))
                f_segment_avg_10s = np.zeros((dequeues_len, n_channels))
                r_segment_avg_10s = np.zeros((dequeues_len, n_channels))
                dict_avg_10s = {-1: [f_segment_avg_10s, r_segment_avg_10s, n_freq_event, n_rare_event],
                                0: [f_segment_avg_10s, r_segment_avg_10s, n_freq_event, n_rare_event]}
                # sent msg for plotter (to make it reset everything too)
                avg_outlet.push_chunk(r_segment_avg.tolist(), 0.00001)
                avg_outlet.push_chunk(f_segment_avg.tolist(), 0.00001)
                if RECORDING:
                    # recreate logs
                    log_eeg.close()
                    log_evs.close()
                    log_disc.close()
                    log_eeg = open(os.path.join(OUTPUT_PATH, OUTPUT_FILE_EEG), 'w', newline='')
                    log_evs = open(os.path.join(OUTPUT_PATH, OUTPUT_FILE_EVS), 'w', newline='')
                    log_disc = open(os.path.join(OUTPUT_PATH, OUTPUT_FILE_DISC), 'w', newline='')
                    # recreate the csv writers
                    eeg_writer = csv.writer(log_eeg)
                    evs_writer = csv.writer(log_evs)
                    disc_writer = csv.writer(log_disc)
                print("done!")
                continue  # goes to next iteration
            if sample.count(0) == len(sample):  # all elements are 0 ==> closing condition
                break  # exit the while cycle
            if data_segment[-1] == 0:  # i.e. first time printed something in this cycle (or after restart)
                print("Receiving data...")
            if SELECTED_CHANNELS:
                sample = [sample[i] for i in labels_ids]  # remove extra channels
            if DEBUG_PRINT:
                if data_segment[-1] == 0:
                    print("")
                print("EEG data: ")
                print("\ttimestamp: " + str(data_time))
                print("\tsample: " + str(sample))
                print("----------------------------------------")
                print("Marker data: ")
                print("\ttimestamp: " + str(marker_time))
                print("\tevent: " + str(marker))
                print("===========================================================")

            if RECORDING:
                # EEG csv
                if data_segment[-1] == 0:  # i.e. first sample
                    data_time = 0.0  # needed since lsl can't send timestamp == 0
                row = [data_time] + sample
                eeg_writer.writerow(row)
                # evs csv
                if marker is not None:
                    row = [marker_time] + [marker]
                    evs_writer.writerow(row)

            # updates EEG timestamp and data in dequeues
            data_segment.append(sample)
            time_segment.append(data_time)
            data_segment.popleft()
            time_segment.popleft()

            # Check if current segment is the right one to update the rare or frequent averaged potentials---------------------------

            # first check (first two rows in if): sample related to first event to be processed is in right position (i.e. event aligned)
            # second check (last row in if): not having old dirty values belonging to discarded data
            # OBS: need check we got a least new <dequeues_len> samples but, since we perform avg only if sample related to stimulus
            # is in position <samples_pre_ev> (i.e. elements from position <samples_pre_ev> to end have been rewritten), to align all
            # events and having desired interval of pause_pre_ev, event_length and pause_post_ev, then we just have to check that
            # first <samples_pre_ev> samples have been rewritten (i.e. != 0) to perform avg:

            # rare case
            if (len(r_events) > 0 and
                (r_events[0] - (1 / srate) + 0.001 < time_segment[samples_pre_ev] < r_events[0] + (1 / srate) - 0.001)) \
                    and ((not USING_CONSOLE) or ((np.array(time_segment)[:samples_pre_ev] == 0).sum() == 0)):
                # valid segment --> used in avg --> need to filter it!
                data_array = np.array(data_segment)
                for i in range(n_channels):
                    avg_padded[int(srate):dequeues_len + int(srate)] = data_array[:, i]  # fill padded segment for filter
                    avg_padded = dsp.convolve(avg_padded, fir, mode="same")  # applying band-pass filter
                    avg_padded = dsp.filtfilt(b_notch, a_notch, avg_padded)  # applying notch filter
                    data_array[:, i] = avg_padded[int(srate):dequeues_len + int(srate)]  # recover filtered data
                # call avg function on current segment
                r_segment_avg, n_rare_event = avg(data_array, r_segment_avg, n_rare_event)
                if DEBUG_PRINT:
                    print("Avg updated with rare event n° " + str(n_rare_event) + ", occurred at " + str(r_events[0]) + "s")
                    print("avg: " + str(r_segment_avg))
                    print("time: " + str(r_events[0]))
                    print("===========================================================")
                else:
                    sys.stdout.write(
                        "\rAvg updated with rare event n° {}, occurred at {}s".format(n_rare_event, r_events[0]))
                    sys.stdout.flush()
                if USING_CONSOLE:
                    # update the dictionary
                    dict_avg_10s[data_time] = [f_segment_avg, r_segment_avg, n_freq_event, n_rare_event]
                    keys = list(dict_avg_10s.keys())
                    discardable = [i for i in keys if data_time - i > 10]
                    for key in discardable[0:-1]:
                        dict_avg_10s.pop(key)  # remove entry if too old
                    if DEBUG_PRINT:
                        count = 0
                        for k in list(dict_avg_10s.keys()):
                            print(str(count) + "\tkey: " + str(k) + "\t" + str(dict_avg_10s.get(k)[0][0][0]))
                            count += 1
                        print("===========================================================")
                # send msg to plot avg for all channels
                avg_outlet.push_chunk(r_segment_avg.tolist(), -r_events[0])
                r_events.pop(0)  # remove this event from list

            # frequent case
            elif (len(f_events) > 0 and
                  (f_events[0] - (1 / srate) + 0.001 < time_segment[samples_pre_ev] < f_events[0] + (1 / srate) - 0.001)) \
                    and ((not USING_CONSOLE) or ((np.array(time_segment)[:samples_pre_ev] == 0).sum() == 0)):
                # valid segment --> used in avg --> need to filter it!
                data_array = np.array(data_segment)
                for i in range(n_channels):
                    avg_padded[int(srate):dequeues_len + int(srate)] = data_array[:, i]  # fill padded segment for filter
                    avg_padded = dsp.convolve(avg_padded, fir, mode="same")  # applying band-pass filter
                    avg_padded = dsp.filtfilt(b_notch, a_notch, avg_padded)  # applying notch filter
                    data_array[:, i] = avg_padded[int(srate):dequeues_len + int(srate)]  # recover filtered data
                # call avg function on current segment
                f_segment_avg, n_freq_event = avg(data_array, f_segment_avg, n_freq_event)
                if DEBUG_PRINT:
                    print("Avg updated with frequent event n° " + str(n_freq_event) + ", occurred at " + str(f_events[0]) + "s")
                    print("avg: " + str(f_segment_avg))
                    print("time: " + str(f_events[0]))
                    print("===========================================================")
                else:
                    sys.stdout.write("\rAvg updated with frequent event n° {}, occurred at {}s".format(n_freq_event, f_events[0]))
                    sys.stdout.flush()
                if USING_CONSOLE:
                    # update the dictionary
                    dict_avg_10s[data_time] = [f_segment_avg, r_segment_avg, n_freq_event, n_rare_event]
                    keys = list(dict_avg_10s.keys())
                    discardable = [i for i in keys if data_time - i > 10]
                    for key in discardable[0:-1]:
                        dict_avg_10s.pop(key)  # remove entry if too old
                    if DEBUG_PRINT:
                        count = 0
                        for k in list(dict_avg_10s.keys()):
                            print(str(count) + "\tkey: " + str(k) + "\t" + str(dict_avg_10s.get(k)[0][0][0]))
                            count += 1
                        print("===========================================================")
                # send msg to plot avg for all channels
                avg_outlet.push_chunk(f_segment_avg.tolist(), f_events[0])
                f_events.pop(0)  # remove this event from list

            # Check if current marker represents an event ---------------------------------------------------------------------------
            if marker is not None:
                if marker[0] == 'R':  # rare stimulus
                    r_events.append(marker_time)
                else:  # frequent stimulus
                    f_events.append(marker_time)
            # OBS: with this code, if a new rare event takes place before obtaining right segment for previous one,
            # then we'll continue looking for the right segment for the first one to occur, then we'll do the same
            # for second one and so on (i.e. possible to overlap two segments)

            # Check if lost some samples --------------------------------------------------------------------------------------------
            if time_segment[-1] > round(time_segment[-2] + (1 / srate) + 0.0001, 5 - len(str(int(time_segment[-2])))) and \
                    time_segment[-2] != 0:
                # OBS: actual time > previous time + time step (=1/srate) +  offset, where latter rounded according to its value
                if not DEBUG_PRINT:
                    sys.stdout.write("\n")
                print("\033[1;31;48m" + "Lost or invalid sample! Check the terminal of the Sender to see if an 'invalid"
                      " sample' print is present; if not, the sample has been lost" + "\033[1;37;0m" +  # code to have red print
                      " previous timestamp: {}, current one: {}".format(time_segment[-2], time_segment[-1]))
                if DEBUG_PRINT:
                    print("")

            # Discard msg case ------------------------------------------------------------------------------------------------------
            if USING_CONSOLE:
                msg, timestamp = console_inlet.pull_sample(timeout=0)
                if msg is not None and msg[0] == 'DISCARD':
                    # reset averaged potentials and n of events back to the ones characterizing first entry of dict (i.e. oldest one)
                    first_key = list(dict_avg_10s.keys())[0]
                    f_segment_avg, r_segment_avg, n_freq_event, n_rare_event = dict_avg_10s.get(first_key)
                    # reset list of event to be processed, since seconds have been discarded
                    f_events = []
                    r_events = []
                    # reset time dequeue, used to check if got rid of dirty values, belonging to discarded data, before computing avg
                    time_segment = deque([0 for _ in range(dequeues_len)])
                    # send msg to plot reset avg for all channels
                    timestamp = first_key-(pause_post_ev+event_length) if first_key-(pause_post_ev+event_length) > 0 else 0.00001
                    avg_outlet.push_chunk(r_segment_avg.tolist(), 0.00001)
                    avg_outlet.push_chunk(f_segment_avg.tolist(), timestamp)
                    if DEBUG_PRINT:
                        print("Segments after DISCARD: " + str(first_key))
                        print("f_segment: " + str(f_segment_avg[0][0]))
                        print("r_segment: " + str(r_segment_avg[0][0]))
                    if RECORDING:
                        row = [first_key + (1/srate)] + [data_time]  # both extremes has to be included in removal
                        disc_writer.writerow(row)

        except (pylsl.pylsl.LostError, pylsl.pylsl.TimeoutError):  # i.e. if connection lost
            sys.stdout.write("\n")
            print("Connection lost with one or more streams!")
            print("Closing streams...", end=" ")
            data_inlet.close_stream()
            marker_inlet.close_stream()
            if USING_CONSOLE:
                console_inlet.close_stream()
            print("done!")
            if RECORDING:
                print("Closing csv file...", end=" ")
                log_eeg.close()
                log_evs.close()
                log_disc.close()
                print("done!")
            sys.exit()

    sys.stdout.write("\n")
    print("Session ended!")
    print("Closing streams...", end=" ")
    data_inlet.close_stream()
    marker_inlet.close_stream()
    print("done!")
    if RECORDING:
        print("Closing csv file...", end=" ")
        log_eeg.close()
        log_evs.close()
        log_disc.close()
        print("done!")
    # send final msg to plotter
    zero_chunk = np.zeros((dequeues_len, n_channels))
    avg_outlet.push_chunk(zero_chunk.tolist(), 0.0)
    # wait for console ack or closing input
    if USING_CONSOLE:
        while True:
            msg, timestamp = console_inlet.pull_sample()  # blocking call
            if msg is not None and msg[0] == 'CLOSE_ALL':
                break
    else:
        input("Press enter to terminate the program when the plotter has finished!")


if __name__ == '__main__':
    main(sys.argv[1:])
