'''
    Unicorn.py
    ---------------
    Wrapper around the free C API to access g.Tec Unicorn-bi EEG headset
    Implements the same interface as g.Tec's Unicorn Python API
    Tested by running g.Tec's UnicornPythonAcquisitionExample.py

    See ./Lib/unicorn.h for explanatory comments

'''

import platform
import struct
import os
from typing import List
from ctypes import (
    CDLL, cast, byref, pointer, POINTER, 
    c_char, c_size_t, c_bool, c_int, c_char_p, c_ulonglong, c_float, c_uint32, c_uint8
)
from unicorn_defines import (
NULL_P,
UNICORN_SUPPORTED_DEVICE_VERSION,
UNICORN_RECOMMENDED_BLUETOOTH_DEVICE_NAME,
UNICORN_RECOMMENDED_BLUETOOTH_DEVICE_MANUFACTURER,
#
UNICORN_ERROR_SUCCESS,
UNICORN_ERROR_INVALID_PARAMETER,
UNICORN_ERROR_BLUETOOTH_INIT_FAILED,
UNICORN_ERROR_BLUETOOTH_SOCKET_FAILED,
UNICORN_ERROR_OPEN_DEVICE_FAILED,
UNICORN_ERROR_INVALID_CONFIGURATION,
UNICORN_ERROR_BUFFER_OVERFLOW,
UNICORN_ERROR_BUFFER_UNDERFLOW,
UNICORN_ERROR_OPERATION_NOT_ALLOWED,
UNICORN_ERROR_CONNECTION_PROBLEM,
UNICORN_ERROR_UNSUPPORTED_DEVICE,
UNICORN_ERROR_INVALID_HANDLE,
UNICORN_ERROR_GENERAL_ERROR,
#
UNICORN_SERIAL_LENGTH_MAX,
UNICORN_DEVICE_VERSION_LENGTH_MAX,
UNICORN_FIRMWARE_VERSION_LENGTH_MAX,
UNICORN_STRING_LENGTH_MAX,
UNICORN_SAMPLING_RATE,
UNICORN_EEG_CHANNELS_COUNT,
UNICORN_ACCELEROMETER_CHANNELS_COUNT,
UNICORN_GYROSCOPE_CHANNELS_COUNT,
UNICORN_TOTAL_CHANNELS_COUNT,
UNICORN_EEG_CONFIG_INDEX,
UNICORN_ACCELEROMETER_CONFIG_INDEX,
UNICORN_GYROSCOPE_CONFIG_INDEX,
UNICORN_BATTERY_CONFIG_INDEX,
UNICORN_COUNTER_CONFIG_INDEX,
UNICORN_VALIDATION_CONFIG_INDEX,
UNICORN_NUMBER_OF_DIGITAL_OUTPUTS,
#
UNICORN_HANDLE_T,
UNICORN_DEVICE_SERIAL_T,
UNICORN_DEVICE_VERSION_T,
UNICORN_FIRMWARE_VERSION_T,
UNICORN_AMPLIFIER_CHANNEL_T,
UNICORN_AMPLIFIER_CONFIGURATION_T,
UNICORN_DEVICE_INFORMATION_T,
UNICORN_BLUETOOTH_ADAPTER_INFO_T,
)

module_path = os.path.split(__file__)[0]
if platform.system() == "Windows":
    unicornlib = CDLL(os.path.join(module_path, "Lib", "Win32", "Unicorn.dll"))
else:
    unicornlib = CDLL(os.path.join(module_path, "Lib", "Linux", "libunicorn.so"))


# --- CONSTANTS

SupportedDeviceVersion = UNICORN_SUPPORTED_DEVICE_VERSION  # The Unicorn device version that is valid for this API
RecommendedDeviceName = UNICORN_RECOMMENDED_BLUETOOTH_DEVICE_NAME  # The device name of the recommended (delivered) Bluetooth adapter
RecommendedDeviceManufacturer = UNICORN_RECOMMENDED_BLUETOOTH_DEVICE_MANUFACTURER  # The manufacturer of the recommended (delivered) Bluetooth adapter

ErrorSuccess = UNICORN_ERROR_SUCCESS  # The operation completed successfully. No error occurred
ErrorInvalidParameter = UNICORN_ERROR_INVALID_PARAMETER  # One of the specified parameters does not contain a valid value
ErrorBluetoothInitFailed = UNICORN_ERROR_BLUETOOTH_INIT_FAILED  # The initialization of the Bluetooth adapter failed
ErrorBluetoothSocketFailed = UNICORN_ERROR_BLUETOOTH_SOCKET_FAILED  # The operation could not be performed because the Bluetooth socket failed
ErrorOpenDeviceFailed = UNICORN_ERROR_OPEN_DEVICE_FAILED  # The device could not be opened
ErrorInvalidConfiguration = UNICORN_ERROR_INVALID_CONFIGURATION  # The configuration is invalid
ErrorBufferOverflow = UNICORN_ERROR_BUFFER_OVERFLOW  # The acquisition buffer is full
ErrorBufferUnderflow = UNICORN_ERROR_BUFFER_UNDERFLOW  # The acquisition buffer is empty
ErrorOperationNotAllowed = UNICORN_ERROR_OPERATION_NOT_ALLOWED  # The operation is not allowed during acquisition or non-acquisition
ErrorConnectionProblem = UNICORN_ERROR_CONNECTION_PROBLEM  # The operation could not complete because of connection problems
ErrorUnsupportedDevice = UNICORN_ERROR_UNSUPPORTED_DEVICE  # The device is not supported with this API’s SupportedDeviceVersion
ErrorInvalidHandle = UNICORN_ERROR_INVALID_HANDLE  # The specified Unicorn handle is invalid
ErrorUnknownError = UNICORN_ERROR_GENERAL_ERROR  # An unspecified error occurred

SerialLengthMax = UNICORN_SERIAL_LENGTH_MAX  # The maximum length of the serial number, including the terminating null character
DeviceVersionLengthMax = UNICORN_DEVICE_VERSION_LENGTH_MAX  # The maximum length of the device version, including the terminating null character
FirmwareVersionLengthMax = UNICORN_FIRMWARE_VERSION_LENGTH_MAX  # The maximum length of the firmware version, including the terminating null character
StringLengthMax = UNICORN_STRING_LENGTH_MAX  # The maximum string length
SamplingRate = UNICORN_SAMPLING_RATE  # The sampling rate of the Unicorn Brain Interface
EEGChannelsCount = UNICORN_EEG_CHANNELS_COUNT  # The number of available EEG channels
AccelerometerChannelsCount = UNICORN_ACCELEROMETER_CHANNELS_COUNT  # The number of available accelerometer channel
GyroscopeChannelsCount = UNICORN_GYROSCOPE_CHANNELS_COUNT  # The number of available gyroscope channel
TotalChannelsCount = UNICORN_TOTAL_CHANNELS_COUNT  # The total number of available channels
EEGConfigIndex = UNICORN_EEG_CONFIG_INDEX  # The index of the first EEG AmplifierChannel in AmplifierConfiguration.Channels
AccelerometerConfigIndex = UNICORN_ACCELEROMETER_CONFIG_INDEX  # The index of the first accelerometer AmplifierChannel in AmplifierConfiguration.Channels
GyroscopeConfigIndex = UNICORN_GYROSCOPE_CONFIG_INDEX  # The index of the first gyroscope AmplifierChannel in AmplifierConfiguration.Channels
BatteryConfigIndex = UNICORN_BATTERY_CONFIG_INDEX  # The index of the Battery AmplifierChannel in AmplifierConfiguration.Channels
CounterConfigIndex = UNICORN_COUNTER_CONFIG_INDEX  # The index of the Counter AmplifierChannel in AmplifierConfiguration.Channels
ValidationConfigIndex = UNICORN_VALIDATION_CONFIG_INDEX  # The index of the Validation Indicator AmplifierChannel in AmplifierConfiguration.Channels
NumberOfDigitalOutputs = UNICORN_NUMBER_OF_DIGITAL_OUTPUTS  # The number of digital output channels

# TODO should (a subset of) these variable be attributes of the class Unicorn?

# --- EXCEPTIONS

class DeviceException (Exception):
    """Exception raised for errors in the input.

    Attributes:
        error_code -- integer error code emitted from the C API
        context_message -- sttring to provide extra information to the user

    Usage:
        try:
            # ...
            raise DeviceException(4, "Raised while opening device #2")
        except DeviceException as error:
            print(str(error)) # OPEN DEVICE FAILED: <more text>. Raised while opening device #2.
            print(f"Error code: {error.error_code:02x}" # Error code: 04
    """

    _error_description = {
        UNICORN_ERROR_SUCCESS:                  "SUCCESS",
        UNICORN_ERROR_INVALID_PARAMETER:        "INVALID PARAMETER",
        UNICORN_ERROR_BLUETOOTH_INIT_FAILED:    "BLUETOOTH INIT FAILED",
        UNICORN_ERROR_BLUETOOTH_SOCKET_FAILED:  "BLUETOOTH SOCKET FAILED",
        UNICORN_ERROR_OPEN_DEVICE_FAILED:       "OPEN DEVICE FAILED",
        UNICORN_ERROR_INVALID_CONFIGURATION:    "INVALID CONFIGURATION",
        UNICORN_ERROR_BUFFER_OVERFLOW:          "BUFFER OVERFLOW",
        UNICORN_ERROR_BUFFER_UNDERFLOW:         "BUFFER UNDERFLOW",
        UNICORN_ERROR_OPERATION_NOT_ALLOWED:    "OPERATION NOT_ALLOWED",
        UNICORN_ERROR_CONNECTION_PROBLEM:       "CONNECTION PROBLEM",
        UNICORN_ERROR_UNSUPPORTED_DEVICE:       "UNSUPPORTED DEVICE",
        UNICORN_ERROR_INVALID_HANDLE:           "INVALID HANDLE",
        UNICORN_ERROR_GENERAL_ERROR:            "GENERAL ERROR",
    }
    

    def __init__(self, error_code, context_message=None):
        self.error_code = error_code
        self.error_descr = self._error_description.get(error_code, UNICORN_ERROR_GENERAL_ERROR)
        self.error_text = _GetLastErrorText() 
        self.context_message = context_message
        self.message = f"{self.error_descr}: {self.error_text}" + ("" if self.context_message is None else f" {self.context_message}.")

    def __str__(self):
        return str(self.message) # __str__() obviously expects a string to be returned, so make sure not to send any other data types

    # FIXME never used the original Unicorn library, cannot know whether this implementation has the same behavior



# --- STRUCTURES (CLASSES)

class AmplifierChannel:
    Name = ""
    Unit = ""
    Range = [0,0]
    Enabled = False
    _c_struct = None
    
    def __init__(self, UNICORN_AMPLIFIER_CHANNEL: UNICORN_AMPLIFIER_CHANNEL_T  = None, 
                    name=None, unit=None, range_=None, enabled=None):
            if UNICORN_AMPLIFIER_CHANNEL is not None:
                self._c_struct = UNICORN_AMPLIFIER_CHANNEL
                self.Name = UNICORN_AMPLIFIER_CHANNEL.name.decode('utf-8')
                self.Unit = UNICORN_AMPLIFIER_CHANNEL.unit.decode('utf-8')
                self.Range = [UNICORN_AMPLIFIER_CHANNEL.range[ii] for ii in range(2)] 
                self.Enabled = UNICORN_AMPLIFIER_CHANNEL.enabled
            else:
                if name is not None:
                    self.Name = name
                if unit is not None:
                    self.Unit = unit
                if range is not None:
                    self.Range = range_
                if enabled is not None:
                    self.Enabled = enabled                

    # @classmethod
    # def from_attributes(cls, name="", unit="", range=[0,0], enabled=False):
    #     return cls(name=Name, unit=Unit, range=Range, enabled=Enabled)

    # @classmethod
    # # call: amp_chan = AmplifierChannel.from_c_struct(UNICORN_AMPLIFIER_CHANNEL)
    # def from_c_struct(cls, UNICORN_AMPLIFIER_CHANNEL: UNICORN_AMPLIFIER_CHANNEL_T):
    #         Name = UNICORN_AMPLIFIER_CHANNEL.name.decode('utf-8')
    #         Unit = UNICORN_AMPLIFIER_CHANNEL.unit.decode('utf-8')
    #         Range = [UNICORN_AMPLIFIER_CHANNEL.range[ii] for ii in range(2)] 
    #         Enabled = UNICORN_AMPLIFIER_CHANNEL.enabled
    #         return cls(name=Name, unit=Unit, range=Range, enabled=Enabled)

    # @classmethod
    # # call: dummy_chan = AmplifierChannel.dummy()
    # def dummy(cls, index=None):
    #         Name = "Ch" if index==None else f"Ch{index}"
    #         Unit = "a.u."
    #         Range = [0,1] 
    #         Enabled = False
    #         return cls(name=Name, unit=Unit, range=Range, enabled=Enabled)
    
    def c_struct(self, update_attribute=True) -> UNICORN_BLUETOOTH_ADAPTER_INFO_T:
        # TODO: method untested!!
        cstruct = UNICORN_BLUETOOTH_ADAPTER_INFO_T()
        cstruct.name = self.Name.encode('utf-8')
        cstruct.unit = self.Unit.encode('utf-8')
        cstruct.range =  (c_float * 2)(*self.Range)
        cstruct.enabled = c_bool(self.Enabled)
        if update_attribute:
            self._c_struct = cstruct
        return cstruct

    def __repr__(self):
        return( "AmplifierChannel(None,"
            f"{self.Name}, {self.Unit}, {self.Range}, "
            f"{'' if self.Enabled else 'not '}enabled"
            ")" 
            )
    
    
class AmplifierConfiguration:
    AmplifierChannels = []
    _c_struct = None

    def __init__(self, UNICORN_AMPLIFIER_CONFIGURATION: UNICORN_AMPLIFIER_CONFIGURATION_T  = None, 
                    amp_chan_list: List[AmplifierChannel] = None):
        if UNICORN_AMPLIFIER_CONFIGURATION is not None:
            amp_chan_list = []
            for channel_c_struct in UNICORN_AMPLIFIER_CONFIGURATION.Channels:
                amp_chan_list.append(AmplifierChannel(channel_c_struct))
            self._c_struct = UNICORN_AMPLIFIER_CONFIGURATION
        #               
        self.AmplifierChannels = amp_chan_list

    # @classmethod
    # # call: amp_chan = AmplifierConfiguration.from_c_struct(UNICORN_AMPLIFIER_CONFIGURATION)
    # def from_c_struct(cls, UNICORN_AMPLIFIER_CONFIGURATION: UNICORN_AMPLIFIER_CONFIGURATION_T, achan_list: List[AmplifierChannel] = None):
    #     AmplifierChannels = [ 
    #         AmplifierChannel.from_c_struct(UNICORN_AMPLIFIER_CONFIGURATION.Channels[ii]) for ii in range(UNICORN_TOTAL_CHANNELS_COUNT)
    #     ]
    #     return cls(AmplifierChannels)
    
    @classmethod
    # call: dummy_config = AmplifierConfiguration.dummy()
    def dummy(cls):
        # Dummy configuration
        AmplifierChannels = [
            AmplifierChannel(name=f"Ch{ii:02d}") for ii in range(TotalChannelsCount)
            ]
        return cls(AmplifierChannels)
    
    def c_struct(self, update_attribute:bool=False) -> UNICORN_AMPLIFIER_CONFIGURATION_T:
        cstruct = UNICORN_AMPLIFIER_CONFIGURATION_T()
        for ii,amp_chan in enumerate(self.AmplifierChannels):
            cstruct.Channels[ii] = amp_chan.c_struct
        if update_attribute:
            self._c_struct = cstruct
        return cstruct
    
    def __repr__(self):
        return( "AmplifierConfiguration(\\\n" +\
        "\\\n".join([f"{1+ii}: {repr(self.AmplifierChannels[ii])}" for ii in range(len(self.AmplifierChannels))]) +\
        "\\\n)" 
        )



class BluetoothAdapterInfo:
    def __init__(self, UNICORN_BLUETOOTH_ADAPTER_INFO: UNICORN_BLUETOOTH_ADAPTER_INFO_T):
        self.Name = UNICORN_BLUETOOTH_ADAPTER_INFO.name.decode('utf-8')
        self.Manufacturer = UNICORN_BLUETOOTH_ADAPTER_INFO.manufacturer.decode('utf-8')
        self.IsRecommendedDevice = UNICORN_BLUETOOTH_ADAPTER_INFO.isRecommendedDevice
        self.HasProblem = UNICORN_BLUETOOTH_ADAPTER_INFO.hasProblem
        self._c_struct = UNICORN_BLUETOOTH_ADAPTER_INFO

    def c_struct(self):
        # bai = UNICORN_BLUETOOTH_ADAPTER_INFO_T()
        # bai.name = self.Name.encode('utf-8')
        # bai.manufacturer = self.Manufacturer.encode('utf-8')
        # bai.isRecommendedDevice = c_bool(self.IsRecommendedDevice)
        # bai.hasProblem = c_bool(self.HasProblem)
        # return bai
        return self._c_struct

    def __repr__(self):
        #FIXME __repr__ cannot initialize object
        return( "BluetoothAdapterInfo("
            f"({self.Name}, {self.Manufacturer}, "
            f"{'is ' if self.IsRecommendedDevice else 'not '}recommended, "
            f"{'has ' if self.HasProblem else 'no '}problem"
            ")" 
            )


class DeviceInformation:
    def __init__(self, UNICORN_DEVICE_INFORMATION: UNICORN_DEVICE_INFORMATION_T):
        self.NumberOfEegChannels = UNICORN_DEVICE_INFORMATION.numberOfEegChannels
        self.Serial = UNICORN_DEVICE_INFORMATION.serial.decode('ascii')
        self.FwVersion = UNICORN_DEVICE_INFORMATION.firmwareVersion.decode('ascii')
        self.DeviceVersion = UNICORN_DEVICE_INFORMATION.deviceVersion.decode('ascii')
        # pcbVer = UNICORN_DEVICE_INFORMATION.pcbVersion
        # self.PcbVersion = (c_char*len(pcbVer))(*bytearray(pcbVer)).value.decode('ascii')
        self.PcbVersion = bytearray(UNICORN_DEVICE_INFORMATION.pcbVersion).decode('ascii')
        self.EnclosureVersion = bytearray(UNICORN_DEVICE_INFORMATION.enclosureVersion).decode('ascii')

    def c_struct(self): 
        raise Exception("Method of DeviceInformation.c_struct() not yetimplemented")
        # TODO: implement c_struct method for class DeviceInformation (or not?)

    def __repr__(self):
        #FIXME __repr__ cannot initialize object
        return( "DeviceInformation("
            f"({self.NumberOfEegChannels} chans, Serial: {self.Serial}, "
            f"FW: {self.FwVersion}, Ver: {self.DeviceVersion}, "
            f"PCB: {self.PcbVersion}, Encl: {self.EnclosureVersion}"
             ")" 
            )        





# --- C API WRAPPER FUNCTIONS FOR CLASS STATIC METHODS


# def manage_error(errorCode, raise_exception=True) -> None:
#     if errorCode:
#         c_GetLastErrorText = unicornlib.UNICORN_GetLastErrorText
#         c_GetLastErrorText.restype = c_char_p
#         errTxt = c_GetLastErrorText()
#         # error_text = c_char_p(errTxt).value.decode('utf-8')
#         error_text = errTxt.decode('utf-8')
#         if raise_exception:
#             raise DeviceException(error_text, errorCode)
#         else:
#             print("Error: ", error_text, f"(code {errorCode})")
#     return None


def GetApiVersion() -> float:
# UNICORN_API float UNICORN_GetApiVersion();
    c_GetApiVersion = unicornlib.UNICORN_GetLastErrorText
    c_GetApiVersion.restype = c_float
    version = c_GetApiVersion()
    # FIXME: it seems to return random numbers
    # print("version: ", version)
    return version


def _GetLastErrorText() -> str:
    c_GetLastErrorText = unicornlib.UNICORN_GetLastErrorText
    c_GetLastErrorText.restype = c_char_p
    errTxt = c_GetLastErrorText()
    # error_text = c_char_p(errTxt).value.decode('utf-8')
    error_text = errTxt.decode('utf-8')
    return error_text


def GetBluetoothAdapterInfo() -> BluetoothAdapterInfo:
# UNICORN_API int UNICORN_GetBluetoothAdapterInfo(UNICORN_BLUETOOTH_ADAPTER_INFO* bluetoothAdapterInfo);
    c_GetBluetoothAdapterInfo = unicornlib.UNICORN_GetBluetoothAdapterInfo
    c_GetBluetoothAdapterInfo.argtypes = ( POINTER(UNICORN_BLUETOOTH_ADAPTER_INFO_T), )
    bluetoothAdapterInfo = UNICORN_BLUETOOTH_ADAPTER_INFO_T(b"", b"", False, False)
    errorCode = c_GetBluetoothAdapterInfo(byref(bluetoothAdapterInfo))
    if errorCode:
        raise DeviceException(errorCode)
    bt_info = BluetoothAdapterInfo(bluetoothAdapterInfo)
    # print("err:", errorCode, " bt_info:", bt_info)
    # manage_error(errorCode)
    return bt_info


def GetAvailableDevices(only_paired: bool):# -> List(str):
    '''Scans for available devices.
    !!STUB DOCSTRING, TAKEN FROM THE C HEADER!!

	Discovers available paired or unpaired devices. Estimates the number of available paired or unpaired devices and returns information about discovered devices.

	onlyPaired           	Defines whether only paired devices or only unpaired
									devices should be returned. If only unpaired devices
									should be returned, an extensive device scan is performed.
									An extensive device scan takes a rather long time. In the
									meantime, the Bluetooth adapter and the application are
									blocked. Scanning for paired devices only can be executed
									faster. If  TRUE, only paired devices are discovered. If
									 FALSE, only unpaired devices can be discovered.
    Returns:
	availableDevices			A pointer to the beginning of an array of
									UNICORN_DEVICE_SERIAL, which receives available
									devices when the method returns. If NULL is passed, the
									number of available devices is returned only to determine
									the amount of memory to allocate.

	Raises		An error code is returned as integer if scanning for available devices fails.
    '''
    # TODO better docstrings for all functions 

    c_GetAvailableDevices = unicornlib.UNICORN_GetAvailableDevices
    c_GetAvailableDevices.argtypes = POINTER(POINTER(c_char)), POINTER(c_size_t), c_bool
    c_GetAvailableDevices.restype = c_int

    availableDevicesCount = c_size_t(0)
    onlyPaired = c_bool(only_paired)
    errorCode = c_GetAvailableDevices(POINTER(POINTER(c_char))(), byref(availableDevicesCount), onlyPaired)
    if errorCode:
        raise DeviceException(errorCode, "Could not count available devices")
    # manage_error(errorCode)
    num_available_devices = availableDevicesCount.value

    availableDevices_t = (c_char * UNICORN_SERIAL_LENGTH_MAX) * num_available_devices
    availableDevices = availableDevices_t() 
    errorCode = c_GetAvailableDevices(cast(availableDevices,POINTER(POINTER(c_char))) , byref(availableDevicesCount), onlyPaired)
    if errorCode:
        raise DeviceException(errorCode, "Could not retrieve serials of available devices")
    # manage_error(errorCode)
    num_available_devices = availableDevicesCount.value
    device_list = [availableDevices[ii].value.decode('ascii') for ii in range(num_available_devices)]

    # print("err:", errorCode, " count:", num_available_devices, " devices:", device_list)
    return device_list


def IsDeviceLibraryLoadable() -> bool:
    '''not a wrapper, not sure how to implement this'''
    raise Exception("function IsDeviceLibraryLoadable not implemented")
    # TODO: implement function IsDeviceLibraryLoadable?


# --- C API WRAPPER FUNCTIONS FOR OBJECT METHODS

def OpenDevice(device_id:str) -> UNICORN_HANDLE_T:
    # UNICORN_API int UNICORN_OpenDevice(const char* serial, UNICORN_HANDLE_T *hDevice);
    c_OpenDevice = unicornlib.UNICORN_OpenDevice
    c_OpenDevice.argtypes = POINTER(c_char), POINTER(UNICORN_HANDLE_T)
    c_OpenDevice.restype = c_int
    deviceHandle = UNICORN_HANDLE_T()
    deviceId = UNICORN_DEVICE_SERIAL_T()
    deviceId.value = device_id.encode('ascii')
    errorCode = c_OpenDevice(cast(deviceId, POINTER(c_char)), byref(deviceHandle))
    if errorCode:
        raise DeviceException(errorCode)
    # manage_error(errorCode)
    device_handle = deviceHandle.value
    # print("device_id:", device_id, " handle:", device_handle)
    return device_handle


  
def CloseDevice(device_handle: int) -> None:
    # UNICORN_API int UNICORN_CloseDevice(UNICORN_HANDLE *hDevice);
    c_CloseDevice = unicornlib.UNICORN_CloseDevice
    c_CloseDevice.argtypes = POINTER(UNICORN_HANDLE_T),
    c_CloseDevice.restype = c_int
    deviceHandle = UNICORN_HANDLE_T(device_handle)
    errorCode = c_CloseDevice(byref(deviceHandle))
    if errorCode:
        raise DeviceException(errorCode)
    # manage_error(errorCode)
    # print(f"Device {device_handle} closed.")
    return None


def StartAcquisition(device_handle: int, test_signal_enabled:bool) -> None:
    # UNICORN_API int UNICORN_StartAcquisition(UNICORN_HANDLE hDevice, BOOL testSignalEnabled);
    c_StartAcquisition = unicornlib.UNICORN_StartAcquisition
    c_StartAcquisition.argtypes = UNICORN_HANDLE_T, c_bool
    c_StartAcquisition.restype = c_int    
    deviceHandle = UNICORN_HANDLE_T(device_handle)
    errorCode = c_StartAcquisition(deviceHandle, c_bool(test_signal_enabled))
    if errorCode:
        raise DeviceException(errorCode)
    # manage_error(errorCode)
    # print(f"Acquisition started for device {device_handle}.")
    return None


def StopAcquisition(device_handle:int) -> None:
    # UNICORN_API int UNICORN_StopAcquisition(UNICORN_HANDLE hDevice);
    c_StopAcquisition = unicornlib.UNICORN_StopAcquisition
    c_StopAcquisition.argtypes = UNICORN_HANDLE_T, 
    c_StopAcquisition.restype = c_int    
    deviceHandle = UNICORN_HANDLE_T(device_handle)
    errorCode = c_StopAcquisition(deviceHandle)
    if errorCode:
        raise DeviceException(errorCode)
    # manage_error(errorCode)
    # print(f"Acquisition stopped for device {device_handle}.")
    return None

def SetConfiguration(device_handle: int, amp_config: AmplifierConfiguration) -> None:
    # UNICORN_API int UNICORN_SetConfiguration(UNICORN_HANDLE hDevice, UNICORN_AMPLIFIER_CONFIGURATION *configuration);
    c_SetConfiguration = unicornlib.UNICORN_SetConfiguration
    c_SetConfiguration.argtypes = UNICORN_HANDLE_T, UNICORN_AMPLIFIER_CONFIGURATION_T
    c_SetConfiguration.restype = c_int
    deviceHandle = UNICORN_HANDLE_T(device_handle)
    configuration = amp_config.c_struct()
    errorCode = c_SetConfiguration(deviceHandle, byref(configuration))
    if errorCode:
        raise DeviceException(errorCode)
    # manage_error(errorCode)
    print(f"Configuration set device {device_handle}: {repr(amp_config)}.")
    return None


def GetConfiguration(device_handle: int) -> AmplifierConfiguration:
    # UNICORN_API int UNICORN_GetConfiguration(UNICORN_HANDLE hDevice, UNICORN_AMPLIFIER_CONFIGURATION* configuration);
    c_GetConfiguration = unicornlib.UNICORN_GetConfiguration
    c_GetConfiguration.argtypes = UNICORN_HANDLE_T, POINTER(UNICORN_AMPLIFIER_CONFIGURATION_T),
    c_GetConfiguration.restype = c_int
    deviceHandle = UNICORN_HANDLE_T(device_handle)
    configuration = UNICORN_AMPLIFIER_CONFIGURATION_T()
    errorCode = c_GetConfiguration(deviceHandle, byref(configuration))
    amp_config = AmplifierConfiguration(configuration)
    if errorCode:
        raise DeviceException(errorCode)
    # manage_error(errorCode)
    # print(f"Configuration from device {device_handle}: {repr(amp_config)}.")
    return amp_config


def GetData(device_handle: int, number_of_scans: int, destination_buffer: bytearray, destination_buffer_length: int) -> None:
    # UNICORN_API int UNICORN_GetData(UNICORN_HANDLE hDevice, uint32_t numberOfScans, float* destinationBuffer, uint32_t destinationBufferLength);
    assert(len(destination_buffer)==destination_buffer_length)
    c_GetData = unicornlib.UNICORN_GetData
    c_GetData.argtypes = UNICORN_HANDLE_T, c_uint32, POINTER(c_float), c_int,
    c_GetData.restype = c_int
    deviceHandle = UNICORN_HANDLE_T(device_handle)
    SIZE_OF_FLOAT = 4
    float_buffer_t = c_float * (destination_buffer_length // SIZE_OF_FLOAT)

    destinationBuffer = float_buffer_t.from_buffer(destination_buffer)
    # errorCode = c_GetData(deviceHandle, number_of_scans, cast(destinationBuffer, POINTER(c_float)), destination_buffer_length)
    errorCode = c_GetData(deviceHandle, number_of_scans, destinationBuffer, destination_buffer_length)
    if errorCode:
        raise DeviceException(errorCode)
    # manage_error(errorCode)
    # print(f"Received {number_of_scans} scans.")
    return None


def GetChannelIndex(device_handle: int, name: str) -> int:
    # UNICORN_API int UNICORN_GetChannelIndex(UNICORN_HANDLE hDevice, const char *name, uint32_t* channelIndex);
    c_GetChannelIndex = unicornlib.UNICORN_GetChannelIndex
    c_GetChannelIndex.argtypes = UNICORN_HANDLE_T, 
    c_GetChannelIndex.restype = c_int
    deviceHandle = UNICORN_HANDLE_T(device_handle)
    channelIndex = c_uint32()
    errorCode = c_GetChannelIndex(deviceHandle, name, byref(channelIndex))
    if errorCode:
        raise DeviceException(errorCode)
    # manage_error(errorCode)
    chan_index = channelIndex.value
    # print(f"Channel '{name}' has index {chan_index}.")
    return chan_index


def GetNumberOfAcquiredChannels(device_handle: int) -> int:
    # UNICORN_API int UNICORN_GetNumberOfAcquiredChannels(UNICORN_HANDLE hDevice, uint32_t* numberOfAcquiredChannels);
    c_GetNumberOfAcquiredChannels = unicornlib.UNICORN_GetNumberOfAcquiredChannels
    c_GetNumberOfAcquiredChannels.argtypes = UNICORN_HANDLE_T, 
    c_GetNumberOfAcquiredChannels.restype = c_int
    deviceHandle = UNICORN_HANDLE_T(device_handle)
    numberOfAcquiredChannels = c_int()
    errorCode = c_GetNumberOfAcquiredChannels(deviceHandle, byref(numberOfAcquiredChannels))
    if errorCode:
        raise DeviceException(errorCode)
    # manage_error(errorCode)
    num_chans = numberOfAcquiredChannels.value
    # print(f"Acquiring {num_chans} channels for device {device_handle}.")
    return num_chans


def GetDeviceInformation(device_handle: int) -> DeviceInformation:
    # UNICORN_API int UNICORN_GetDeviceInformation(UNICORN_HANDLE hDevice, UNICORN_DEVICE_INFORMATION* deviceInformation);
    c_GetDeviceInformation = unicornlib.UNICORN_GetDeviceInformation
    c_GetDeviceInformation.argtypes = UNICORN_HANDLE_T, POINTER(UNICORN_DEVICE_INFORMATION_T),
    c_GetDeviceInformation.restype = c_int
    deviceHandle = UNICORN_HANDLE_T(device_handle)
    deviceInformation = UNICORN_DEVICE_INFORMATION_T()
    errorCode = c_GetDeviceInformation(deviceHandle, byref(deviceInformation))
    device_info = DeviceInformation(deviceInformation)
    if errorCode:
        raise DeviceException(errorCode)
    # manage_error(errorCode)
    # print(f"Information for device {device_handle}: {repr(device_info)}.")
    return device_info

def SetDigitalOutputs(device_handle: int, digital_outputs: int) -> None:
# UNICORN_API int UNICORN_SetDigitalOutputs(UNICORN_HANDLE hDevice, uint8_t digitalOutputs);
    c_SetDigitalOutputs = unicornlib.UNICORN_SetDigitalOutputs
    c_SetDigitalOutputs.argtypes = UNICORN_HANDLE_T, c_uint8,
    c_SetDigitalOutputs.restype = c_int
    deviceHandle = UNICORN_HANDLE_T(device_handle)
    errorCode = c_SetDigitalOutputs(deviceHandle, digital_outputs & 0xFF)
    if errorCode:
        raise DeviceException(errorCode)
    # manage_error(errorCode)
    # print(f"Set digital outputs for device {device_handle}: {digital_outputs:08b}.")
    return None


def GetDigitalOutputs(device_handle: int) -> int:
    # UNICORN_API int UNICORN_GetDigitalOutputs(UNICORN_HANDLE hDevice, uint8_t* digitalOutputs);
    c_GetDigitalOutputs = unicornlib.UNICORN_GetDigitalOutputs
    c_GetDigitalOutputs.argtypes = UNICORN_HANDLE_T, POINTER(c_uint8),
    c_GetDigitalOutputs.restype = c_int
    deviceHandle = UNICORN_HANDLE_T(device_handle)
    digitalOutputs = c_uint8()
    errorCode = c_GetDigitalOutputs(deviceHandle, byref(digitalOutputs))
    if errorCode:
        raise DeviceException(errorCode)
    # manage_error(errorCode)
    digital_outputs = digitalOutputs.value
    # print(f"Got digital outputs for device {device_handle}: {digital_outputs:08b}.")
    return digital_outputs



# === UTILITIES ===

def scan_format_string(device_handle: int, sep:str=None) -> str:
    amp_config = GetConfiguration(device_handle)
    if sep == None:
        # spaced columns
        fmt_list  = ["{:+7.0f}" for ii in range( 0, 8) if amp_config.AmplifierChannels[ii].Enabled]  # EEG, 8 chans
        fmt_list += ["{:+7.3f}" for ii in range( 8,11) if amp_config.AmplifierChannels[ii].Enabled]  # ACCEL, 3 chans
        fmt_list += ["{:+8.1f}" for ii in range(11,14) if amp_config.AmplifierChannels[ii].Enabled]  # GYRO, 3 chans
        fmt_list += ["{:4.0f}%" for ii in range(14,15) if amp_config.AmplifierChannels[ii].Enabled]  # BATTERY, 1 chan
        fmt_list += ["{:6.0f}"  for ii in range(15,16) if amp_config.AmplifierChannels[ii].Enabled]  # COUNTER, 1 chan
        fmt_list += ["{:3.0f}"  for ii in range(16,17) if amp_config.AmplifierChannels[ii].Enabled]  # VALIDATION, 1 chan
        fmt_str = ' '.join(fmt_list)
    else:
        # tab|comma|etc- separated comumns
        fmt_list  = ["{:.0f}" for ii in range( 0, 8) if amp_config.AmplifierChannels[ii].Enabled]  # EEG, 8 chans
        fmt_list += ["{:.3f}" for ii in range( 8,11) if amp_config.AmplifierChannels[ii].Enabled]  # ACCEL, 3 chans
        fmt_list += ["{:.1f}" for ii in range(11,14) if amp_config.AmplifierChannels[ii].Enabled]  # GYRO, 3 chans
        fmt_list += ["{:.0f}%" for ii in range(14,15) if amp_config.AmplifierChannels[ii].Enabled]  # BATTERY, 1 chan
        fmt_list += ["{:.0f}"  for ii in range(15,16) if amp_config.AmplifierChannels[ii].Enabled]  # COUNTER, 1 chan
        fmt_list += ["{:.0f}"  for ii in range(16,17) if amp_config.AmplifierChannels[ii].Enabled]  # VALIDATION, 1 chan
        fmt_str = sep.join(fmt_list)
    return fmt_str



# --- CLASS UNICORN

class Unicorn:

    def __init__(self, serial:str):
        self._valid:bool = False
        self._handle:int = None
        self._serial:str = serial
        try:
            self._handle = OpenDevice(serial)
        except DeviceException as err:
            print(err)
        if self._handle:
            self._valid = True

    def __del__(self):
       if self._valid:
           CloseDevice(self._handle)

    def _check_valid(self):
        if not self._valid:
            raise Exception ("Unicorn object not initialized")

    def _close_device(self):
        self._check_valid()
        CloseDevice(self._handle)
        self._valid = False

    def GetChannelIndex(self, name) -> int:
        self._check_valid()
        ch_index = GetChannelIndex(self._handle, name)
        return ch_index

    def GetConfiguration(self) ->  AmplifierConfiguration:
        amp_config = GetConfiguration(self._handle)
        return amp_config
        
    def GetData(self, numberOfScans: int, destinationBuffer: bytearray,  destinationBufferLength: int) -> None:
        GetData(self._handle, numberOfScans, destinationBuffer, destinationBufferLength)
        return None

    def GetDeviceInformation(self) -> DeviceInformation:
        device_info = GetDeviceInformation(self._handle) 
        return device_info

    def GetDigitalOutputs(self) -> int:  # byte?
        digital_outputs = GetDigitalOutputs(self._handle)
        return digital_outputs

    def GetNumberOfAcquiredChannels(self) -> int:
        num_channels = GetNumberOfAcquiredChannels(self._handle)
        return num_channels

    def SetConfiguration(self, configuration: AmplifierConfiguration) -> None:
        SetConfiguration(self._handle, configuration)
        return None

    def SetDigitalOutputs(self, digitalOutputs: int) -> None:
        SetDigitalOutputs(self._handle, digitalOutputs)
        return None

    def StartAcquisition(self, testsignalEnabled: bool) -> None:
        StartAcquisition(self._handle, testsignalEnabled)
        return None

    def StopAcquisition(self) -> None:
        StopAcquisition(self._handle)
        return None
    
    DeviceException = DeviceException  # store DeviceException class as attribute of the class Unicorn




class Unicorn2(Unicorn):
    _num_channels = 0
    _scan_buffer_len = 0
    _num_scans = 0
    _buffer_len = 0
    _data_buffer = None
    _config_info = None

    class ConfigInfo:
        LABELS = (
            [f"EEG {ii+1}" for ii in range(8)] + 
            ["Accelerometer " + "XYZ"[ii] for ii in range(3)] +
            ["Gyroscope " + "XYZ"[ii] for ii in range(3)] +
            ["Battery Level" + "Counter" + "Validation Indicator"]
        )
        SHORT_LABELS = (
            [f"EEG{ii+1}" for ii in range(8)] + 
            ["Acc"+"XYZ"[ii] for ii in range(3)] +
            ["Gyr" + "XYZ"[ii] for ii in range(3)] +
            ["Bat"] + ["Cnt"] + ["Val"]
        )
        EEG_LABELS_1020 = ["Fz", "C3", "Cz", "C4", "Pz", "PO7", "Oz", "PO8"]
        ACCEL_LABELS    = ["Acc"+"XYZ"[ii] for ii in range(3)]
        GYRO_LABELS     = ["Gyr" + "XYZ"[ii] for ii in range(3)]


        eeg_chan_slice = slice(EEGConfigIndex, EEGConfigIndex+EEGChannelsCount, None)
        acc_chan_slice = slice(AccelerometerConfigIndex, AccelerometerConfigIndex+AccelerometerChannelsCount, None)
        gyro_chan_slice = slice(GyroscopeConfigIndex, GyroscopeConfigIndex+GyroscopeChannelsCount, None)
        batt_chan_i = BatteryConfigIndex
        count_chan_i = CounterConfigIndex
        valid_chan_i = ValidationConfigIndex

        CHAN_TYPES = []
        CHAN_TYPES[eeg_chan_slice] = ["EEG"] * EEGChannelsCount
        CHAN_TYPES[acc_chan_slice] = ["ACCEL"] * AccelerometerChannelsCount
        CHAN_TYPES[gyro_chan_slice] = ["GYRO"] * GyroscopeChannelsCount
        CHAN_TYPES[batt_chan_i:] = ["BATT"]
        CHAN_TYPES[count_chan_i:] = ["COUNT"]
        CHAN_TYPES[valid_chan_i:] = ["VALID"]

        amp_config = None
        acq_chan_type = []
        acq_chan_label = []
        slices = {'eeg':None, 'accel':None, 'gyro':None, 'batt':None, 'count':None, 'valid':None}
        def __init__(self, amp_config:AmplifierConfiguration):
            self.amp_config = amp_config
            enabled = [amp_chan.Enabled for amp_chan in self.amp_config.AmplifierChannels]
            self.acq_chan_type = [t for t,e in zip(self.acq_chan_type, enabled) if e]
            self.acq_chan_label = [l for l,e in zip(self.acq_chan_label, enabled) if e]
            try:
                start_eeg = self.acq_chan_type.index("EEG")
            except ValueError:
                start_eeg = 0
            num_eeg = len([t for t in self.acq_chan_type if t=="EEG"])
            try:
                start_accel = self.acq_chan_type.index("ACCEL")
            except ValueError:
                start_accel = 0
            num_accel = len([t for t in self.acq_chan_type if t=="ACCEL"])
            try:
                start_gyro = self.acq_chan_type.index("GYRO")
            except ValueError:
                start_gyro = 0
            num_gyro = len([t for t in self.acq_chan_type if t=="GYRO"])
            try:
                ind_batt, num_batt = self.acq_chan_type.index("BATT"), 1
            except ValueError:
                ind_batt, num_batt = 0, 0
            try:
                ind_count, num_count = self.acq_chan_type.index("COUNT"), 1
            except ValueError:
                ind_count, num_count = 0, 0
            try:
                ind_valid, num_valid = self.acq_chan_type.index("VALID"), 1
            except ValueError:
                ind_valid, num_valid = 0, 0
            self.slices = {
                'eeg':  slice(start_eeg,    start_eeg+num_eeg), 
                'accel':slice(start_accel,  start_accel+num_accel), 
                'gyro': slice(start_gyro,   start_gyro+num_gyro), 
                'batt': slice(ind_batt,     ind_batt+num_batt), 
                'count':slice(ind_count,    ind_count+num_count), 
                'valid':slice(ind_valid,    ind_valid+num_valid),
                }


    def __init__(self, serial:str=None):
        # autoconnect to the first available device
        if not serial:
            deviceList = GetAvailableDevices(True)
            if not deviceList:
                raise Exception (f"{type(self).__name__()} - Autoconnect failed: No paired devices.")
            serial = deviceList[0]
        super().__init__(serial)

    # ---
    def scan_format_string(self, device_handle: int, sep:str=None) -> str:
        fmt_str = scan_format_string(self._handle, sep)
        return fmt_str

    def _allocate_buffer(self, num_scans:int) -> None:
        SIZE_OF_FLOAT = 4
        self._num_scans = num_scans
        self._num_channels = self.GetNumberOfAcquiredChannels()
        self._scan_buffer_len = SIZE_OF_FLOAT * self._num_channels
        self._buffer_len = self._scan_buffer_len * num_scans
        self._data_buffer = bytearray(self._buffer_len)
        return None

    def StartAcquisition(self, testsignalEnabled:bool=False, num_scans:int=SamplingRate//10) -> None:
        self._allocate_buffer(num_scans)
        # TODO scan current configuration and store channel indices and labels
        config_info = self.ConfigInfo(self.GetConfiguration())
        super().StartAcquisition(testsignalEnabled)
        return None

    def SetConfiguration(self, configuration: AmplifierConfiguration) -> None:
        super().SetConfiguration(configuration)
        config_info = self.ConfigInfo(self.GetConfiguration())
        return None        

    def GetDataTuples(self) -> List[tuple]:
        self.GetData(self._num_scans, self._data_buffer, self._buffer_len)
        # # float_buffer = [
        # #     struct.unpack('f'*self._num_channels,  
        # #         self._data_buffer[ss*self._scan_buffer_len:(ss+1)*self._scan_buffer_len]) 
        # #     for ss in range(self._num_scans)
        # #     ]
        # float_buffer = [
        #     struct.unpack_from(
        #         fmt= f"{self._num_channels}f"
        #         buffer=self._data_buffer,
        #         offset = ss*self._scan_buffer_len) 
        #     for ss in range(self._num_scans)
        #     ]

        scan_struct = struct.Struct(f"{self._num_channels}f")
        data_tuples = [
            scan_struct.unpack_from(self._data_buffer, ss*self._scan_buffer_len) 
            for ss in range(self._num_scans)
            ]
        return data_tuples
    
    class DataBlock():
        def __init__(self, data_tuples, config_info=None):
            if config_info:
                slic = config_info.slices
                self.eeg     = [dt[slic['eeg']]     for dt in data_tuples]
                self.accel   = [dt[slic['accel']]   for dt in data_tuples]
                self.gyro    = [dt[slic['gyro']]    for dt in data_tuples]
                self.battery = [dt[slic['batt']]    for dt in data_tuples]
                self.counter = [dt[slic['count']]   for dt in data_tuples]
                self.valid   = [dt[slic['valid']]   for dt in data_tuples]
            else:
                self.eeg     = [dt[0:8]   for dt in data_tuples]
                self.accel   = [dt[8:11]  for dt in data_tuples]
                self.gyro    = [dt[11:14] for dt in data_tuples]
                self.battery = [dt[14]    for dt in data_tuples]
                self.counter = [dt[15]    for dt in data_tuples]
                self.valid   = [dt[16]    for dt in data_tuples]
        # TODO: prepare labels and print formats


    def GetDataBlock(self) -> DataBlock:
        return self.DataBlock(self.GetDataTuples())
        #return self.DataBlock(self.GetDataTuples(), self._config_info)
