# P300 Real-Time 
Python code to receive EEG signals from the Unicorn Black headset and show the P300 response in real-time. 
In order to obtain this response, we will present a set of stimuli according to the oddball paradigm. 

The system has five main processes that will run simultaneously, using LabStreamingLayer for communication and data sharing.
These processes can be run on different devices, since LSL broadcasts its streams over the connected network. 

Several combinations of features are offered, such as 4 different stimulation types, the possibility to control the experiment through a console both with or without graphical interface and, besides the real-time analysis already mentioned, it is possible to store the EEG data acquired during the experiment in a csv file for later purposes, such as reproduction, testing or further analysis.

In the developing of the project a local instance has been used.

**Table of Contents**

  * [Preliminary Installation](#preliminary-installation)
      - [Interpreter](#interpreter)
      - [Required Programs](#required-programs)
      - [Required Python Libraries](#required-python-libraries)
  * [File System](#file-system)
  * [Documentation](#documentation)
  * [Execution](#execution)
  * [Limitations and Known Issues](#limitations-and-known-issues)

----------------------------
## Preliminary Installation

### Interpreter

#### - Python >= 3.7, <=3.8 [Windows, Linux/UNIX, Mac OS X, Other]

- Can be downloaded from https://www.python.org/downloads/

**Warning**: Make sure to have included the path of the Python folder in the system variable 'path'!

### Required Programs

#### - BrainVision LSL Viewer [Microsoft Windows 10, 64-bit] (or equivalent)
To monitor lsl EEG and marker streams online

**Requirements**: Microsoft Visual C++ runtime: Download and install the redistributable `vc_redist.x64.exe` from [here](https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads)

- Download the zip from https://www.brainproducts.com/downloads.php?kid=40&tab=3
- Unpack it and open 'BrainVision_LSL_Viewer_0.9.5.exe'
- Follow the instructions of the installation wizard

### Required Python Libraries

**Tip**: Use a virtual environment to avoid conflicts with other projects!

*For more info:* https://docs.python.org/3/tutorial/venv.html

**Warning**: If you have created a virtual environment, make sure to activate it before installing the following libraries!

- numpy >= 1.16.0: `pip install "numpy>=1.16"`
- scipy >= 1.2.0: `pip install "scipy>=1.2"`
- pandas: `pip install "pandas"`
- pylsl: `pip install "pylsl"`
- matplotlib: `pip install "matplotlib"`
- PySimpleGUI: `pip install "pysimplegui"`
- switch: `pip install "switch"`
- Psychtoolbox: `pip install "psychtoolbox"`
- PsychoPy: `pip install "PsychoPy"`

**Tip**: Simply execute `pip install -r requirements.txt`!

#### Additional steps for Linux
The proposed code can also run on Linux systems, in particular Ubuntu-based ones, once the packages related to the used python libraries have been installed.

First of all, to make LSL work it is necessary to download and install the appropriate version of the `libsls` library, available at https://github.com/sccn/liblsl/releases/tag/v1.15.2.

The remaining missing packages and their installation commands depend mainly on the Linux distribution in use, and may change over time due to related updates, therefore it's not possible to provide a general step-by-step guide; however, thanks to the errors' messages on the terminal, an average Linux user should be able to understand which packages should be installed to move forward. 

### Repository Setup
If the experiment is to be run from offline data, e.g. to perform a simulation, the related dataset should be placed in the data/Datasets folder. This dataset has to have a specific format in order to be compliant with our code. In particular, it has to be a csv file where the
rows contain the observations at each time sample. For each observation we have to know its timestamp (first column), EEG values over all channels (one column per channel), if a stimulation was onset (boolean value, 1 if true), and if this was a rare event (boolean value, 1 if true, 0 if no stimulus or frequent one). Finally, the csv file should not contain any header, i.e. the first observation should be in the first row.
We chose this structure having initially worked with the publicly available dataset found at this [link](https://zenodo.org/record/2649069); to be specific, the `online.csv` file inside the data/Datasets folder is the one recorded from the first subject.

----------------------------

## File System

<!---File system structure + purpose of most relevant files (code, input, output)--->
Our project presents the following folder structure:

    .
    ├── data/   # Data used to run the code
    │   ├── Datasets/   # Dataset csv files
    │   └── Images/     # Images used by the Console script
    ├── code/	# Implemented code and Unicorn libraries
    │   ├── Console/
    |   │   └── Console.py      # Script to control experiment execution
    │   ├── CSV_Merger/
    |   │   └── CSV_Merger.py   # Script to obtain final recording of experiment in single csv file
    │   ├── Plotter/
    |   │   └── Plotter.py      # Script to plot averaged potentials over all channels in real-time 
    │   ├── Receiver/
    |   │   └── Receiver.py     # Script to compute averaged potentials over all channels in real-time
    │   ├── Sender/
    |   │   └── Sender.py       # Script to read and send data from unicorn device or csv file
    │   ├── Stims/  # Scripts to deliver stimuli
    |   │   ├── OddballCheckerboardStim.py      # Visual oddball stimuli delivery with inverting checkerboard
    |   │   ├── ShapeStims.py                   # Visual oddball stimuli delivery with shapes
    |   │   ├── SimpleAudioStims.py             # Auditory oddball stimuli delivery
    |   │   └── VEPCheckboardStim.py            # Pattern reversal stimuli delivery with inverting checkerboard
    │   └── Unicorn/
    │       ├── Lib/ 
    │       |   ├── Linux   # Libraries for Linux
    │       |   └── Win32   # Libraries for Windows
    |       ├── unicorn_defines.py
    |       └── UnicornPy.py
    ├── output/      # Relevant files produced by our code
    │   ├── Plots/      # Final plots of the averaged potentials related to frequent and rare stimuli
    │   └── Recordings/ # csv files with the acquired data
    ├── README.md           # Installation and execution procedures, description of code structure and contents
    └── requirements.txt    # Contains all required python libraries
----------------------------

## Documentation

The complete documentation is available [here](https://drive.google.com/file/d/1hW4gCt0GCw0tHVfOCp67r0oJ4sIJrPE7/view?usp=sharing).  

----------------------------
## Execution

### Set the flags
* `USING_CONSOLE`
  - In Plotter.py, Receiver.py, Sender.py and chosen stimuli script (from code/Stims/, if required by the experiment)
  - To enable the console control 
* `DEBUG_PRINT` 
  - In Console.py (if `USING_CONSOLE == True`); in Plotter.py, Receiver.py, Sender.py and chosen stimuli script (from code/Stims/, if required by the experiment) (if `USING_CONSOLE == False`)
  - To enable verbose prints
* `USE_GUI`
  - In Console.py (if `USING_CONSOLE == True`)
* `USE_DEVICE` 
  - In Sender.py (if `USING_CONSOLE == False`, otherwise overwritten by the console itself, according to the chosen input)
  - To know if used Unicorn device or csv file
  - If False, required to set also values of constants `CSV_FILE`, `SRATE_FILE` and `CHANNEL_NAMES_FILE` 
    - Can be set also as command line arguments (overwriting the values inside the code): `$ python Sender.py -n <csv = file.csv> -s <sampling_rate> -c <channel_names = name_1,...,name_n>`
* `REMOVE_REFERENCE`
  - In Sender.py 
  - To remove reference channel in csv (i.e. required `USE_DEVICE == False`) 
  - If True, required to set also `REFERENCE_COL_N = i`, having the reference channel as the i-th column of the csv file
* `SELECTED_CHANNELS` 
  - In Receiver.py 
  - To compute and plot the averaged potentials of a subset of channels 
  - If True, required to set also `selected_channels = [<ch1>,...,<chn>]`
* `RECORDING`
  - In Receiver.py 
  - To save datasets of the experiments in csv form
    
### Set the constants
* In Receiver.py:
  - `PAUSE_PRE_EV`, `EVENT_LENGTH` and `PAUSE_POST_EV` defining size of window used to calculate aligned averaged potentials 
    - Can be set also as command line arguments (overwriting the values inside the code): `$ python Receiver.py -b <pause_pre_ev> -e <event_length> -p <pause_post_ev>`

### If you want to reproduce a file
* Be sure the csv file is placed in the data/Datasets folder and respects the required formatting 
* If `USING_CONSOLE == False`, set `USE_DEVICE == False` and save the file name inside the constant `CSV_FILE` in the Sender 
  - Can be set also as command line arguments as seen before (overwriting the values inside the code)
* If different from the default values, set also required values for constants `SRATE_FILE` and `CHANNEL_NAMES_FILE`  
  - Can be set also as command line arguments as seen before (overwriting the values inside the code)
  
### Run the scripts
Execute simultaneously Console.py (only if `USING_CONSOLE == True`), Sender.py, Receiver.py, Plotter.py and ShapeStims.py (or another script in the folder code/Stims/, only if `USE_DEVICE == True`)

**Tip**: The scripts can be executed all at the same time through an IDE, or simply one after the other, each in its own terminal (opened in its own directory), through the command `python <script_name>.py <optional_args>`

**Warning**: When using the console, even if we want to reproduce a session from file it is necessary to have Bluetooth on, at least in the initial phase where the Console scans for available Unicorn devices, otherwise we run into the \texttt{BLUETOOTH SOCKET FAILED} error. It is however possible to turn it off once the list has been generated.
**Warning**: When executing the project on two or more computers, it is necessary to always execute the Console and Sender processes on the same device, in order to obtain a correct list of available devices and files as inputs. 

### Commands during execution
Select the input source (only if `USING_CONSOLE == True`) and follow the instruction in the GUI window (or terminal if `USE_GUI == False`). Use the commands
- Play: start the acquisition
- Pause: pause the acquisition
- Stop: stop the acquisition and prepare to reset everything (by pressing play again)
- Discard (only if `USE_DEVICE == True`): discard the last 10 seconds of the acquisition
- Quit: end the processing
- Help (only if `USE_GUI = False`): shows the available commands to control the acquisition.

### Outputs generated at the end of the processing
The plot of the averaged potentials is saved in the folder output/Plots with the current timestamp. Three csv with the current timestamp are generated in a folder stored in output/Recordings.
- disc_session: csv of the discarded intervals
- eeg_session: csv with the raw EEG data
- evs_session: csv with the stimuli marks

It is possible to combine the three csv in a single one, by executing the CSV_Merger script: `$ python CSV_Merger.py <experiment_timestamp> <srate> <n_channels>` 

----------------------------

## Limitations and Known Issues
- In the Unicorn documentation it is explicitly written that the Bluetooth Dongle given with the Unicorn Hybrid Black device should be used. For all our tests and acquisition we did not use this dongle, but it is strongly recommended maintaining the Unicorn device close to the laptop in order to reduce the possibility of losing data.  Moreover, any amount of Bluetooth devices close to the working station may cause connection instability (data loss, validation or failed connection).
- We  tried  to  run  the  code  on  Ubuntu  20.04  after  modifying  the  libraries  appropriately,  however  we  were  unable to pair the Unicorn Hybrid Black with the laptop. 
  The device was visible but when we tried to connect them it returned an error message "Pairing failed". 
  Also, once back on Windows, we had to disconnect and reconnect the headset several times before it worked properly.
- In the initialization phase, the window containing the graphs may become unresponsive; thus, the user will not be able to move and/or resize it (or doing so would result in the "not responsive" message, and/or the whitish overlay of the window). However, as soon as the Plotter starts updating the window, it will recover any error, and any resizing and/or moving operation will be allowed without causing any problem (however, the window is never very responsive, and the user may wait a few seconds before getting the desired effect).
- By pressing any of the console buttons we buffer a command on the stream; this means that by pressing the same button many times in a row we might cause a desynchronization across the processes, which will need to elaborate each of the given prompts and end up complying with the last command only after a few cycles.
- The audio stimulation might have issues with bluetooth headsets.
- When moving the window of the markers, the generation of the stimuli is paused and the window is frozen. This may cause some irregularity in the first stimulus after releasing the window. It is recommended to pause the acquisition during the motion of the window.
