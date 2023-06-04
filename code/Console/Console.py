import os
from os import listdir
from os.path import isfile
from time import sleep

import PySimpleGUI as sg
import pylsl
import switch as switch
from pylsl import StreamInlet, StreamOutlet, resolve_byprop, StreamInfo

DATA_PATH = os.path.join("..", "Unicorn")
import sys
sys.path.insert(0, DATA_PATH)
import UnicornPy

DEBUG_PRINT = False
USE_GUI = True
USE_DEVICE = True

#===================== THEME SETTINGS =======================================
sg.theme('black')

button_background='#1d1d1d' #dark grey
text_color='#00cca3' #turquoise
text_font='Consolas' #code style
#===========================================================================

FILES_PATH = os.path.join("..", "..", "data", "Datasets")
IMAGES_PATH = os.path.join("..", "..", "data", "Images")

image_play = os.path.join(IMAGES_PATH, 'play.png')
image_pause = os.path.join(IMAGES_PATH, 'pause.png')
image_stop = os.path.join(IMAGES_PATH, 'stop.png')
image_discard = os.path.join(IMAGES_PATH, 'discard.png')
image_loading = os.path.join(IMAGES_PATH, 'unicorn.png')
image_setup = os.path.join(IMAGES_PATH, 'unicorn.png')
gif_loading = os.path.join( IMAGES_PATH, 'loading1.gif')
gif_connecting = os.path.join(IMAGES_PATH, 'connecting.gif')
gif_closing = os.path.join(IMAGES_PATH, 'closing.gif')

name = 'Console'
type = 'text'


def place(elem):
    '''
    Places element provided into a Column element so that its placement in the layout is retained.
    :param elem: the element to put into the layout
    :return: A column element containing the provided element
    '''
    return sg.Column([[elem]], pad=(0,0))


def available_devices():
    '''
    This function scans for Unicorn devices.
    It uses the function GetAvailableDevices(bool) from UnicornPy, where bool changes with respect to the operating system.
    - on Linux True rescan and False check only paired
    - on Windows True for only paired and False for only unpaired
    :return: deviceList
    '''
    try:
        # Get available device serials.
        deviceList = UnicornPy.GetAvailableDevices(True)
        # On Linux True rescan and False check only paired
        # On Windows True for only paired and False for only unpaired

        if DEBUG_PRINT:
            # Print available device serials.
            print("Available devices:")
            i = 0
            for device in deviceList:
                print("#%i %s" % (i, device))
                i += 1
    except UnicornPy.DeviceException as e:
        print(e)
    except Exception as e:
        print("An unknown error occured. %s" % e)

    input_window(deviceList)


def input_window(deviceList):
    '''
    This window gives the user the possibility to choose the EEG source (file or device) and (To Do) the stimulus
    nature. It scans the available devices and files. By default sets True the last source
    TODO for further works: Add the possibility to choose the stimulus nature

    :param deviceList:
    :return:
    '''

    global USE_DEVICE

    info = StreamInfo(name, type, 1, 0, 'string')
    console_outlet = StreamOutlet(info)

    sleep(1)  # Necessary to give the other processes the time to found console_outlet
    # Get all files in the directory FILES_PATH
    files = [f for f in listdir(FILES_PATH) if isfile(os.path.join(FILES_PATH, f))]

    if USE_GUI:
        # Insert the image saved in image_loading
        layout_setup = [[sg.Image(image_setup)],
                          [sg.Text('Available devices:', text_color=text_color, font=text_font)]]

        # If no devices are found
        if deviceList == []:
            layout_setup.append([sg.Text('No device available. Please pair with a Unicorn first.', text_color=text_color, font=text_font)])

        # Generate a RadioButton for each device found
        for device in deviceList:
            layout_setup.append([sg.Radio(device, 'DEVICE', text_color=text_color, font=text_font, key=device, default=True)])

        layout_setup.append([sg.Text('', text_color=text_color, font=text_font)])
        layout_setup.append([sg.Text('Available files:', text_color=text_color, font=text_font)])

        # If no files are found
        if files == []:
            layout_setup.append([sg.Text('No files available.', text_color=text_color, font=text_font)])

        # Generate a RadioButton for each file found
        for f in files:
            layout_setup.append([sg.Radio(f, 'DEVICE', text_color=text_color, font=text_font, key=f, default=True)])

        # CONFIRM button
        layout_setup.append([sg.Button('Confirm', button_color=text_color, font=text_font)])

        # Generate the window
        window = sg.Window('Set up', layout_setup)

        while True:
            event, values = window.read(timeout=100)

            # Scan all the RadioButtons to check which element is selected and save it in selected_input
            for device in deviceList:
                if values[device]:
                    selected_input = device
                    break
            for file in files:
                if values[file]:
                    selected_input = file
                    break

            if event == sg.WINDOW_CLOSED or event == 'Confirm':
                console_outlet.push_sample([selected_input]) # Streams the name of the selected source
                break

        # Finish up by removing from the screen
        window.close()

        if selected_input in deviceList:
            USE_DEVICE = True
            connecting_window(console_outlet)
        else:
            USE_DEVICE = False
            loading_window(console_outlet)

    else:
        sleep(0.1)
        if not files == []:
            # Print available device serials.
            print("\nAvailable files:")
            i = 0
            for file in files:
                print("#%i %s" % (i, file))
                i += 1
        else:
            print("No file available.")

        if not deviceList == []:
            # Print available device serials.
            print("\nAvailable devices:")
            i = len(files)
            for device in deviceList:
                print("#%i %s" % (i, device))
                i += 1
        else:
            print("No device available")

        sources = files+deviceList

        valid_source = False

        while not valid_source:
            # Request device selection.
            print()
            selected_input = int(input("Select source by ID #"))
            if selected_input < 0 or selected_input > len(sources)-1:
                print("Index out of range. Please select a valid source")
                i = 0
                for source in sources:
                    print("#%i %s" % (i, source))
                    i += 1
            else:
                valid_source = True
                selected_input = sources[selected_input]
                if selected_input in deviceList:
                    USE_DEVICE = True
                else:
                    USE_DEVICE = False
                console_outlet.push_sample([selected_input])  # Streams the name of the selected source
                print("\nSelected input:", selected_input, "\n==============================\n")
                loading_window(console_outlet)


def connecting_window(console_outlet):
    '''
    Simple window with an animated gif until the device is correctly connected
    :param console_outlet:
    :return:
    '''
    # Insert the image saved in image_loading
    layout_connecting = [[sg.Text('Connecting to Unicorn device...', text_color=text_color, font=text_font)],
                         [sg.Image(gif_connecting, key='_GIF_')]]

    # Generate the window
    window = sg.Window('Connecting...', layout_connecting)

    while True:
        event, values = window.read(timeout=1) #don't set the timeout to 0

        # Update the animated gif
        window['_GIF_'].update_animation(gif_connecting, time_between_frames=30)

        # Look for all the streams with name "Data"
        data_streams = resolve_byprop('name', 'Data', timeout=0)  # Look for a reasonable Stream
        if data_streams != []:  # If a Stream is foung
            # Connect to the stream and read
            data_inlet = StreamInlet(data_streams[0], recover=False)
            msg, timestamp = data_inlet.pull_sample(timeout=10)
            if not msg == None and msg[0] == 'OK': # If the message "OK" is received from the stream, the device is connected and we can proceed
                break

    # Finish up by removing from the screen
    window.close()
    loading_window(console_outlet)


def loading_window(console_outlet):
    '''
    This window provides information about the status of the connections between process and allows the user
    to decide whether start the recording
    :param console_outlet:
    :return:
    '''

    # ======== Initialize the flag variables ===========
    stream_EEG_found = False
    stream_markers_found = False
    stream_plotter_found = False
    stream_receiver_found = False
    stream_sender_created = True
    # ==================== Done ========================

    text = ""

    if USE_GUI:
        # Create the layout for the window
        layout_loading = [[sg.Image(image_loading, key='_LOADING_')],
                          [sg.Text('Creating a stream... ', text_color=text_color, font=text_font),
                           sg.Text('Done!', text_color=text_color, font=text_font, key='_SENDER-STREAM_', visible=stream_sender_created)],
                          [sg.Text('Looking for a EEG stream... ', text_color=text_color, font=text_font),
                           sg.Text('Found!', text_color=text_color, font=text_font, key='_EEG-STREAM_', visible=stream_EEG_found)],
                          [sg.Text('Looking for a markers stream... ', text_color=text_color, font=text_font, visible=USE_DEVICE),
                           sg.Text('Found!', text_color=text_color, font=text_font, key='_MARKERS-STREAM_', visible=stream_markers_found)],
                          [sg.Text('Looking for a plotter stream... ', text_color=text_color, font=text_font),
                           sg.Text('Found!', text_color=text_color, font=text_font, key='_PLOTTER-STREAM_', visible=stream_plotter_found)],
                          [place(sg.Text('Looking for a receiver stream... ', text_color=text_color, font=text_font)),
                           place(sg.Text('Found!', text_color=text_color, font=text_font, key='_RECEIVER-STREAM_',
                                         visible=stream_receiver_found)),
                           place(sg.Button('Next', button_color=text_color, font=text_font))]]

        # Add the layout to the window
        window = sg.Window('Connecting', layout_loading)

    else:
        print("Connecting to the streams...")

    if USE_GUI:
        while True:
            event, values = window.read(timeout=1) #don't set the timeout to 0

            ''' We never enter here
            if not stream_sender_created:
                info = StreamInfo(name, type, 1, 0, 'string')
                outlet = StreamOutlet(info)
                stream_sender_created=True
                window['_SENDER-STREAM_'].Update(visible=stream_sender_created) #Render the "Done!" text'''

            if not stream_EEG_found:    #Check whether the Stream was found
                data_streams = resolve_byprop('name', 'Data', timeout=0)    #Look for a reasonable Stream
                if data_streams != []:  #If a Stream is foung
                    data_inlet = StreamInlet(data_streams[0], recover=False)
                    msg, timestamp = data_inlet.pull_sample(timeout=10)
                    if not msg == None and msg[0] == 'OK':  #If an OK is received, then the Stream is ready and we can pass
                        if DEBUG_PRINT: print("Data OK")
                        stream_EEG_found=True
                        if USE_GUI:
                            window['_EEG-STREAM_'].Update(visible=stream_EEG_found) # Render the "Found!"
                        #data_inlet.close_stream()   # Close the stream

            if not stream_markers_found and USE_DEVICE:
                markers_streams = resolve_byprop('name', 'Markers', timeout=0)
                if markers_streams != []:
                    marker_inlet = StreamInlet(markers_streams[0], recover=False)
                    msg, timestamp = marker_inlet.pull_sample(timeout=10)
                    if not msg == None and msg[0] == 'OK':
                        if DEBUG_PRINT: print("Markers OK")
                        stream_markers_found = True
                        if USE_GUI:
                            window['_MARKERS-STREAM_'].Update(visible=stream_markers_found)
                        marker_inlet.close_stream()

            if not stream_plotter_found:
                plotter_streams = resolve_byprop('name', 'Plotter', timeout=0)
                if plotter_streams != []:
                    plotter_inlet = StreamInlet(plotter_streams[0], recover=False)
                    msg, timestamp = plotter_inlet.pull_sample(timeout=10)
                    if not msg == None and msg[0] == 'OK':
                        if DEBUG_PRINT: print("Plotter OK")
                        stream_plotter_found=True
                        if USE_GUI:
                            window['_PLOTTER-STREAM_'].Update(visible=stream_plotter_found)
                        #plotter_inlet.close_stream()

            if not stream_receiver_found:
                receiver_streams = resolve_byprop('name', 'Receiver', timeout=0)
                if receiver_streams != []:
                    receiver_inlet = StreamInlet(receiver_streams[0], recover=False)
                    msg, timestamp = receiver_inlet.pull_sample(timeout=10)
                    if not msg == None and msg[0]=='OK':
                        if DEBUG_PRINT: print("Receiver OK")
                        stream_receiver_found = True
                        if USE_GUI:
                            window['_RECEIVER-STREAM_'].Update(visible=stream_receiver_found)
                        receiver_inlet.close_stream()

            if event == sg.WINDOW_CLOSED or event == 'Next':
                console_outlet.push_sample(['NEXT'])
                break

        # Finish up by removing from the screen
        window.close()

    else:
        plotter_streams = resolve_byprop('name', 'Plotter', timeout=pylsl.FOREVER)
        if plotter_streams != []:
            plotter_inlet = StreamInlet(plotter_streams[0], recover=False)

        data_streams = resolve_byprop('name', 'Data', timeout=pylsl.FOREVER)
        if data_streams != []:
            data_inlet = StreamInlet(data_streams[0], recover=False)

        input("Press enter when all the streams are ready!")
        console_outlet.push_sample(['NEXT'])

    console_window(console_outlet, plotter_inlet, data_inlet)


def console_window(console_outlet, plotter_inlet, data_inlet):
    '''
    This window provides three buttons for play/pause, stop and discard (10 seconds) the recording.
    TODO for further works: Add battery status in case of device
    TODO for further works: Add textarea for debug
    :param console_outlet:
    :return:
    '''

    if USE_GUI:
        # Create the layout fow the window
        layout = [[sg.Button(use_ttk_buttons=True, button_color=(button_background, sg.theme_background_color()), key='_PP_',
                             image_filename=image_play),
                   sg.Button(use_ttk_buttons=True, button_color=(button_background, sg.theme_background_color()), key='_STOP_',
                             image_filename=image_stop, disabled=True),
                   sg.Button(use_ttk_buttons=True, button_color=(button_background, sg.theme_background_color()), key='_DISCARD_',
                             image_filename=image_discard, disabled=True)]]

        # Create the form and show it without the plot
        window = sg.Window('P300 RealTime', layout, finalize=True,
                           element_justification='center', font='Helvetica 18')

        # Flag needed to switch between play and pause
        # True -> PLAY
        # False -> PAUSE
        toggle = True
        # Switchable image
        image_pp = image_pause

        # Display and interact with the Window using an Event Loop
        while True:
            event, values = window.read(timeout=0)

            if not USE_DEVICE:
                msg, timestamp = data_inlet.pull_sample(timeout=0)
                if not msg == None and msg[0] == 'EOF':
                    if DEBUG_PRINT: print("End of file reached")
                    sg.popup('End of file reached', text_color=text_color, font=text_font, keep_on_top=True, non_blocking=False)
                    break

            if event == '_PP_':
                if DEBUG_PRINT: print("PP")

                if toggle: console_outlet.push_sample(['PLAY'])
                else: console_outlet.push_sample(['PAUSE'])
                window['_PP_'].Update(image_filename=image_pp)
                window['_STOP_'].Update(disabled=toggle)
                window['_DISCARD_'].Update(disabled=not USE_DEVICE)

                if not toggle: image_pp = image_pause
                else: image_pp = image_play
                toggle = not toggle

            elif event == '_STOP_':
                if DEBUG_PRINT: print("Stop")
                console_outlet.push_sample(['STOP'])
                window['_DISCARD_'].Update(disabled=True)
                window['_STOP_'].Update(disabled=True)

            elif event == '_DISCARD_':
                if DEBUG_PRINT: print("Discard")
                console_outlet.push_sample(['DISCARD'])

            # See if user wants to quit or window was closed
            if event == sg.WINDOW_CLOSED:
                console_outlet.push_sample(['QUIT'])
                break

        # Finish up by removing from the screen
        window.close()
        closing_window(console_outlet, plotter_inlet)

    else: # If do not use graphic
        text_first = "List of commands:\n\tPLAY (or A) to start the acquisition\n\tPAUSE (or P) to pause the acquisition\n\tSTOP (or S) to reset all"
        text_discard = "\n\tDISCARD (or D) to discard the last 10 seconds"
        text_second = "\n\tQUIT (or Q) to terminate the process\n\tHELP (or H) to repeat this message"
        init_s = "Digit PLAY or A to start the acquisition: "
        state = "init"

        if USE_DEVICE:
            text = text_first + text_discard + text_second
        else:
            text = text_first + text_second
        print()
        print(text)
        if not USE_DEVICE:
            print("**Check whether the end of file is reached by checking the Sender terminal, then press Q**\n")
        else:
            print()
        while True:
            if not USE_DEVICE:
                msg, timestamp = data_inlet.pull_sample(timeout=0)
                if not msg == None and msg[0] == 'EOF':
                    print('End of file reached!')
                    break
            if state == "init":
                cmd = input(init_s).upper()
            else:
                cmd = input(state + " state - " + "Command: ").upper()
            with switch.Switch(cmd) as case:
                if case("QUIT", "Q"):
                    console_outlet.push_sample(['QUIT'])
                    break
                elif case("HELP", "H"):
                    print(text)
                else:
                    if state == "init":
                        if case("PLAY", "A"):
                            console_outlet.push_sample(['PLAY'])
                            state = "Playing"
                        elif case("PAUSE", "P"):
                            pass
                        elif case("STOP", "S"):
                            pass
                        elif case("DISCARD", "D") and USE_DEVICE:
                            pass
                        else:
                            print("Unkown command. Digit HELP or H to see the available commands.")
                    elif state == "Playing":
                        if case("PLAY", "A"):
                            pass
                        elif case("PAUSE", "P"):
                            console_outlet.push_sample(['PAUSE'])
                            state = "Pause"
                        elif case("STOP", "S"):
                            pass
                        elif case("DISCARD", "D") and USE_DEVICE:
                            console_outlet.push_sample(['DISCARD'])
                        else:
                            print("Unkown command. Digit HELP or H to see the available commands.")
                    elif state == "Pause":
                        if case("PLAY", "A"):
                            console_outlet.push_sample(['PLAY'])
                            state = "Playing"
                        elif case("PAUSE", "P"):
                            pass
                        elif case("STOP", "S"):
                            console_outlet.push_sample(['STOP'])
                            state = "Stop"
                        elif case("DISCARD", "D") and USE_DEVICE:
                            console_outlet.push_sample(['DISCARD'])
                        else:
                            print("Unkown command. Digit HELP or H to see the available commands.")
                    elif state == "Stop":
                        if case("PLAY", "A"):
                            console_outlet.push_sample(['PLAY'])
                            state = "Playing"
                        elif case("PAUSE", "P"):
                            pass
                        elif case("STOP", "S"):
                            pass
                        elif case("DISCARD", "D") and USE_DEVICE:
                            pass
                        else:
                            print("Unkown command. Digit HELP or H to see the available commands.")

        closing_window(console_outlet, plotter_inlet)


def closing_window(console_outlet, plotter_inlet):
    '''
        Simple window with an animated gif until the device is correctly connected
        :param console_outlet:
        :return:
        '''

    if USE_GUI:
        # Insert the image saved in image_loading
        layout_closing = [[sg.Text('Saving the results...', text_color=text_color, font=text_font)],
                             [sg.Image(gif_closing, key='_GIF_')]]

        # Generate the window
        window = sg.Window('Closing...', layout_closing)

        while True:
            event, values = window.read(timeout=1)  # Don't set the timeout to 0

            msg, timestamp = plotter_inlet.pull_sample(timeout=0)
            if not msg == None and msg[0] == 'DONE':
                if DEBUG_PRINT: print("Plotter has finished")
                console_outlet.push_sample(["CLOSE_ALL"])
                break

            # Update the animated gif
            window['_GIF_'].update_animation(gif_closing, time_between_frames=30)

        # Finish up by removing from the screen
        window.close()
    else:
        while True:
            msg, timestamp = plotter_inlet.pull_sample(timeout=0)
            if not msg == None and msg[0] == 'DONE':
                if DEBUG_PRINT: print("Plotter has finished")
                input("Press enter to close all")
                console_outlet.push_sample(["CLOSE_ALL"])
                break


def main():
    available_devices()


if __name__ == "__main__":
    main()
