#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Alternating inverting checkerboard stimuli. Presented at 0.5 seconds interval.
LabStreamingLayer is integrated to stream event markers.

This script was generated with the PsychoPy Builder and then modified to deliver event marker through
LabStreamingLayer. """

from __future__ import absolute_import, division

import argparse
import os  # handy system and path functions
import sys  # to get file system encoding

from pylsl import StreamInlet, StreamInfo, StreamOutlet, resolve_stream

DATA_PATH = os.path.join("..", "Unicorn")
sys.path.insert(0, DATA_PATH)
import UnicornPy

USING_CONSOLE = True

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
    from psychopy import visual, core, data, logging
    from psychopy.constants import (NOT_STARTED, STARTED, FINISHED)
    from psychopy.hardware import keyboard
    import pylsl

    parser = argparse.ArgumentParser()
    parser.add_argument("--n_reps", "-n", help="Number of times we repeat the stimuli (0 for infinite)", type=int,
                        default=0, metavar='\b')
    parser.add_argument("--stim_len", "-t", help="Stimulus duration in seconds", type=float, default=0.5, metavar='\b')
    parser.add_argument("--light_theme", "-c", help="Flag to activate light theme", action="store_true")
    args = parser.parse_args()

    # set the color scheme values
    if args.light_theme:
        win_color = [0.54, 0.81, 0.94]
        stim_color = 'white'
        color_space = 'rgb'
    else:
        win_color = 'black'
        stim_color = [17, 225, 183]
        color_space = 'rgb255'

    # initialize stim repeats
    if args.n_reps == 0:
        args.n_reps = 10000

    # initialization to invert the checkerboard
    invert_idx = 0

    # initialize the LSL stream
    info = StreamInfo('MarkerStream', 'Markers', 1, 0, 'string')
    outlet_marker = StreamOutlet(info)

    logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

    endExpNow = False  # flag for 'escape' or other condition => quit the exp
    frameTolerance = 0.001  # how close to onset before 'same' frame

    # Setup the Window
    # size, fullscreen and screen should be adjusted according to the user's needs
    # By default, it opens a non fullscreen window in your second monitor
    win = visual.Window(
        size=(1280, 720), fullscr=False, screen=1,
        winType='pyglet', allowGUI=True, allowStencil=False,
        monitor='testMonitor', color=win_color, colorSpace=color_space,
        blendMode='avg', useFBO=True,
        units='height')

    # create a default keyboard (e.g. to check for escape)
    defaultKeyboard = keyboard.Keyboard()

    # Initialize components for Routine "trial"
    trialClock = core.Clock()
    # we use the grating visual stimulus with squareXsquare textures to generate the checkerboard
    grating = visual.GratingStim(
        win=win, name='grating',
        tex='sqrXsqr', mask=None,
        ori=0.0, pos=(0.0, 0.0), size=(2, 2), sf=[16, 16], phase=0.5,
        color=[1, 1, 1], colorSpace='rgb',
        opacity=None, contrast=1.0, blendmode='avg',
        texRes=256.0, interpolate=True, depth=0.0)

    # set up handler to look after randomisation of conditions etc
    trials = data.TrialHandler(nReps=args.n_reps, method='random', originPath=-1, trialList=[None], seed=None,
                               name='trials')
    thisTrial = trials.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisTrial.rgb)
    if thisTrial != None:
        for paramName in thisTrial:
            exec('{} = thisTrial[paramName]'.format(paramName))

    if not USING_CONSOLE:
        # Create some timers
        globalClock = core.Clock()  # to track the time since experiment started
        routineTimer = core.CountdownTimer()  # to track time remaining of each (non-slip) routine

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
                    # Create some timers
                    globalClock = core.Clock()  # to track the time since experiment started
                    routineTimer = core.CountdownTimer()  # to track time remaining of each (non-slip) routine
                    break
                if msg is not None and msg[0] == "QUIT":
                    core.quit()

        for thisTrial in trials:
            currentLoop = trials
            # abbreviate parameter names if possible (e.g. rgb = thisTrial.rgb)
            if thisTrial != None:
                for paramName in thisTrial:
                    exec('{} = thisTrial[paramName]'.format(paramName))

            # ------Prepare to start Routine "trial"-------

            if USING_CONSOLE:
                # Check the console stream for command messages
                msg, timestamp = console_inlet.pull_sample(timeout=0)
                # enter the pause state
                if msg is not None and msg[0] == "PAUSE":
                    pause = True
                    win.flip()  # stop drawing
                    # store time to resume later
                    currentRoutineTime = routineTimer.getTime()
                    currentGlobalTime = globalClock.getTime()
                    currentTrialTime = trialClock.getTime()
                    pauseClock = core.Clock()  # record how much time we stayed paused
                    while pause:
                        msg, timestamp = console_inlet.pull_sample(timeout=0)
                        if msg is not None and msg[0] == "PLAY":
                            # resume play and restore clock
                            globalClock.reset()
                            globalClock.add(-currentGlobalTime)
                            pauseTime = pauseClock.getTime()
                            routineTimer.add(pauseTime)
                            trialClock.reset()
                            trialClock.add(-currentTrialTime)
                            pause = False
                        if msg is not None and msg[0] == "STOP":
                            # break out of the message checking loop and stop
                            play = False
                            invert_idx = 0  # restart the indexing of the invert list
                            # TODO: Possibly delete this if it is useless
                            break
                            # return
                        if msg is not None and msg[0] == "QUIT":
                            # quit the program
                            core.quit()
                # second break to escape out of the repetition loop and restart our stims
                if not play:
                    break
            # invert the checkerboard colors
            if invert_idx == 0:
                grating.color = 'black'
                invert_idx = 1
                event_marker = "F"
            elif invert_idx == 1:
                grating.color = 'white'
                invert_idx = 0
                event_marker = "R"

            continueRoutine = True
            routineTimer.add(args.stim_len)

            # update component parameters for each repeat
            # keep track of which components have finished
            trialComponents = [grating]
            for thisComponent in trialComponents:
                thisComponent.tStart = None
                thisComponent.tStop = None
                thisComponent.tStartRefresh = None
                thisComponent.tStopRefresh = None
                if hasattr(thisComponent, 'status'):
                    thisComponent.status = NOT_STARTED
            # reset timers
            t = 0
            _timeToFirstFrame = win.getFutureFlipTime(clock="now")
            trialClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
            frameN = -1

            # -------Run Routine "trial"-------
            while continueRoutine and routineTimer.getTime() > 0:
                # get current time
                t = trialClock.getTime()
                tThisFlip = win.getFutureFlipTime(clock=trialClock)
                tThisFlipGlobal = win.getFutureFlipTime(clock=None)
                frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
                # update/draw components on each frame

                # *grating* updates
                if grating.status == NOT_STARTED and tThisFlip >= 0 - frameTolerance:
                    # keep track of start time/frame for later
                    grating.frameNStart = frameN  # exact frame index
                    grating.tStart = t  # local t and not account for scr refresh
                    grating.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(grating, 'tStartRefresh')  # time at next scr refresh
                    grating.setAutoDraw(True)
                    outlet_marker.push_sample(event_marker, globalClock.getTime())
                if grating.status == STARTED:
                    # is it time to stop? (based on global clock, using actual start)
                    if tThisFlipGlobal > grating.tStartRefresh + args.stim_len - frameTolerance:
                        # keep track of stop time/frame for later
                        grating.tStop = t  # not accounting for scr refresh
                        grating.frameNStop = frameN  # exact frame index
                        win.timeOnFlip(grating, 'tStopRefresh')  # time at next scr refresh
                        grating.setAutoDraw(False)

                # check for quit (typically the Esc key)
                if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
                    core.quit()

                # check if all components have finished
                if not continueRoutine:  # a component has requested a forced-end of Routine
                    break
                continueRoutine = False  # will revert to True if at least one component still running
                for thisComponent in trialComponents:
                    if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                        continueRoutine = True
                        break  # at least one component has not yet finished

                # refresh the screen
                if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                    win.flip()

            # -------Ending Routine "trial"-------
            for thisComponent in trialComponents:
                if hasattr(thisComponent, "setAutoDraw"):
                    thisComponent.setAutoDraw(False)
            trials.addData('grating.started', grating.tStartRefresh)
            trials.addData('grating.stopped', grating.tStopRefresh)
        else:
            # we enter this block after the for loop is exhausted, meaning that we have finished our repetitions
            stop = True

    # completed repeats of 'trials'

    # Flip one final time so any remaining win.callOnFlip()
    # and win.timeOnFlip() tasks get executed before quitting
    win.flip()
    win.close()
    core.quit()


if __name__ == "__main__":
    main()
