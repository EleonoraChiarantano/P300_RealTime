"""Auditory oddball stimuli generation, with integration of the LabStreamingLayer for event marker
streaming """

import argparse
import os
import sys
import time
from random import shuffle

import psychtoolbox as ptb
import pylsl
from psychopy import sound, logging, core
from pylsl import StreamInfo, StreamOutlet, resolve_stream, StreamInlet

DATA_PATH = os.path.join("..", "Unicorn")
sys.path.insert(0, DATA_PATH)
import UnicornPy

USING_CONSOLE = True
DEBUG_PRINT = False

if USING_CONSOLE:
    CONSOLE_PATH = os.path.join("..", "Console")
    sys.path.insert(0, CONSOLE_PATH)
    from Console import DEBUG_PRINT


def main():
    if USING_CONSOLE:
        console_streams = resolve_stream('name', 'Console')
        console_inlet = StreamInlet(console_streams[0], recover=False)

        msg, timestamp = console_inlet.pull_sample()
        source = msg[0]

        deviceList = UnicornPy.GetAvailableDevices(True)

        if source in deviceList:
            start(console_inlet)

        # necessary call for testing without device
        # start(console_inlet)
    else:
        start(None)

def start(console_inlet):

    # suppress warning about sound library, since we are using the best available one anyway
    logging.console.setLevel(logging.CRITICAL)

    parser = argparse.ArgumentParser()
    parser.add_argument("--n_reps", "-n", help="Number of times we repeat the stimuli", type=int, default=80,
                        metavar='\b')
    parser.add_argument("--isi", "-i", help="Inter stimulus interval in seconds", type=float, default=0.5, metavar='\b')
    parser.add_argument("--tone_len", "-t", help="Tone duration in seconds", type=float, default=0.5, metavar='\b')
    args = parser.parse_args()

    offset = 0.0004823  # average time lost by wait function
    # initialize stim repeats
    if args.n_reps == 0:
        args.n_reps = 10000

    # setup the marker stream
    info = StreamInfo('MarkerStream', 'Markers', 1, 0, 'string')
    outlet_marker = StreamOutlet(info)

    # setup the loop and the different tones to be used
    note_list = ['A', 'A', 'A', 'A', 'C', 'A', 'A', 'A']
    notes_idx = 0

    if not USING_CONSOLE:
        # Create some timers
        globalClock = core.Clock()  # to track the time since experiment started

    # ======================= SETUP ===========================
    ''' Continuously sends to the Console a key message ("OK"), to
    confirm that this process is ready to begin the acquisition
    and wait for a key message ("NEXT") from the Console that will
    arrive when all the interested processes are ready '''
    if USING_CONSOLE:
        info_console = StreamInfo('Markers', 'Text', 1, 0, 'string')
        outlet_console = StreamOutlet(info_console)

        console_streams = resolve_stream('name', 'Console')
        console_inlet = StreamInlet(console_streams[0], recover=False)

        print("Ready to stream markers!")

        while True:
            try:
                outlet_console.push_sample(['OK'])
                msg, timestamp = console_inlet.pull_sample(timeout=0)
                if msg is not None and msg[0] == 'NEXT':
                    if DEBUG_PRINT:
                        print(msg[0])
                    break
            except (pylsl.pylsl.LostError, pylsl.pylsl.TimeoutError):
                sys.stdout.write("\n")
                sys.exit()
    # ================== END SETUP ===========================

    # setup flag and loop for stop command
    stop = False
    while not stop:
        # listen for start message
        if USING_CONSOLE:
            while True:
                msg, timestamp = console_inlet.pull_sample(timeout=0)
                if msg is not None and msg[0] == 'PLAY':
                    if DEBUG_PRINT:
                        print(msg[0])
                    play = True
                    globalClock = core.Clock()  # to track the time since experiment started
                    break

        for i in range(args.n_reps):

            if USING_CONSOLE:
                # Check the console stream for possible messages
                msg, timestamp = console_inlet.pull_sample(timeout=0)
                # enter the pause state
                if msg is not None and msg[0] == "PAUSE":
                    pause = True
                    currentGlobalTime = globalClock.getTime() # store time to restore clock after play
                    while pause:
                        msg, timestamp = console_inlet.pull_sample(timeout=0)
                        if msg is not None and msg[0] == "PLAY":
                            # resume play and restore clock
                            globalClock.reset()
                            globalClock.add(-currentGlobalTime)
                            pause = False
                        if msg is not None and msg[0] == "STOP":
                            # break out of the message checking loop and stop
                            play = False
                            notes_idx = 0
                            break
                            # return
                        if msg is not None and msg[0] == "QUIT":
                            sys.exit()
                # second break to escape out of the repetition loop and restart our stims
                if not play:
                    break

            # shuffle the tones each 8 reps, with an additional check to avoid repeating the rare tone
            while note_list[0] == 'C':
                shuffle(note_list)
            mySound = sound.Sound(note_list[notes_idx], secs=args.tone_len)
            event_marker = "F" if note_list[notes_idx] == 'A' else "R"
            notes_idx += 1
            if notes_idx == 8:
                notes_idx = 0
                shuffle(note_list)

            # wait for ISI and then play the toe
            core.wait(args.isi - offset, hogCPUperiod=args.isi - offset)
            now = ptb.GetSecs()
            mySound.play(when=now)
            outlet_marker.push_sample(event_marker, globalClock.getTime())  # send the marker on pylsl
            core.wait(args.tone_len, hogCPUperiod=args.tone_len) # halt execution since tone is on other thread
        else:
            # we enter this block after the for loop is exhausted, meaning that we have finished our repetitions
            stop = True


if __name__ == "__main__":
    main()
