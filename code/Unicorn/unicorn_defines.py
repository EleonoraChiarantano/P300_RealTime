from ctypes import (CDLL, cast, byref, pointer, POINTER, 
    c_char, c_size_t, c_bool, c_int, c_char_p, c_ulonglong, c_float, c_uint16, c_uint8,
    Structure, 
    )

NULL_P = POINTER(c_char)()
# BOOL = c_bool
# FALSE = False
# TRUE = True

# The Unicorn device version that is valid for this API.
UNICORN_SUPPORTED_DEVICE_VERSION = c_char_p(b"1.")

#! The device name of the recommended (delivered) Bluetooth adapter.
UNICORN_RECOMMENDED_BLUETOOTH_DEVICE_NAME = c_char_p(b"CSR8510 A10")

#! The manufacturer of the recommended (delivered) Bluetooth adapter.
UNICORN_RECOMMENDED_BLUETOOTH_DEVICE_MANUFACTURER = c_char_p(b"Cambridge Silicon Radio Ltd.")

# ========================================================================================
# Error Codes
# ========================================================================================

#! The operation completed successfully. No error occurred.
UNICORN_ERROR_SUCCESS = 0

#! One of the specified parameters does not contain a valid value.
UNICORN_ERROR_INVALID_PARAMETER = 1

#! The initialization of the Bluetooth adapter failed.
UNICORN_ERROR_BLUETOOTH_INIT_FAILED = 2

#! The operation could not be performed because the Bluetooth socket failed.
UNICORN_ERROR_BLUETOOTH_SOCKET_FAILED = 3

#! The device could not be opened.
UNICORN_ERROR_OPEN_DEVICE_FAILED = 4

#! The configuration is invalid.
UNICORN_ERROR_INVALID_CONFIGURATION = 5

#! The acquisition buffer is full.
UNICORN_ERROR_BUFFER_OVERFLOW = 6

#! The acquisition buffer is empty.
UNICORN_ERROR_BUFFER_UNDERFLOW = 7

#! The operation is not allowed during acquisition or non-acquisition.
UNICORN_ERROR_OPERATION_NOT_ALLOWED = 8

#! The operation could not complete because of connection problems.
UNICORN_ERROR_CONNECTION_PROBLEM = 9

#! The device is not supported with this API (\ref UNICORN_SUPPORTED_DEVICE_VERSION) 
UNICORN_ERROR_UNSUPPORTED_DEVICE = 10

#! The specified connection handle is invalid.
UNICORN_ERROR_INVALID_HANDLE = 0xFFFFFFFE

#! An unspecified error occurred.
UNICORN_ERROR_GENERAL_ERROR = 0xFFFFFFFF

# ========================================================================================
# Amplifier Properties
# ========================================================================================

#! The maximum length of the serial number.
UNICORN_SERIAL_LENGTH_MAX = 14

#! The maximum length of the device version.
UNICORN_DEVICE_VERSION_LENGTH_MAX = 6

#! The maximum length of the firmware version.
UNICORN_FIRMWARE_VERSION_LENGTH_MAX = 12

#! The maximum string length.
UNICORN_STRING_LENGTH_MAX = 255

#! The sampling rate of the amplifier.
UNICORN_SAMPLING_RATE = 250

#! The number of available EEG channels.
UNICORN_EEG_CHANNELS_COUNT = 8

#! The number of available accelerometer channels.
UNICORN_ACCELEROMETER_CHANNELS_COUNT = 3

#! The number of available gyroscope channels.
UNICORN_GYROSCOPE_CHANNELS_COUNT = 3

#! The total number of available channels.
UNICORN_TOTAL_CHANNELS_COUNT = 17

#! Index of the first EEG \ref UNICORN_AMPLIFIER_CHANNEL in the \ref UNICORN_AMPLIFIER_CONFIGURATION Channels array.
UNICORN_EEG_CONFIG_INDEX = 0

#! Index of the first Accelerometer \ref UNICORN_AMPLIFIER_CHANNEL in the \ref UNICORN_AMPLIFIER_CONFIGURATION Channels array.
UNICORN_ACCELEROMETER_CONFIG_INDEX = 8

#! Index of the first gyroscope \ref UNICORN_AMPLIFIER_CHANNEL in the \ref UNICORN_AMPLIFIER_CONFIGURATION Channels array.
UNICORN_GYROSCOPE_CONFIG_INDEX = 11

#! Index of the battery level \ref UNICORN_AMPLIFIER_CHANNEL in the \ref UNICORN_AMPLIFIER_CONFIGURATION Channels array.
UNICORN_BATTERY_CONFIG_INDEX = 14

#! Index of the counter \ref UNICORN_AMPLIFIER_CHANNEL in the \ref UNICORN_AMPLIFIER_CONFIGURATION Channels array.
UNICORN_COUNTER_CONFIG_INDEX = 15

#! Index of the validation indicator \ref UNICORN_AMPLIFIER_CHANNEL in the \ref UNICORN_AMPLIFIER_CONFIGURATION Channels array.
UNICORN_VALIDATION_CONFIG_INDEX = 16

#! The number of digital output channels.
UNICORN_NUMBER_OF_DIGITAL_OUTPUTS = 8

# ========================================================================================
# Type definitions
# ========================================================================================

#! Type that holds the handle associated with a device.
# typedef uint64_t UNICORN_HANDLE;
UNICORN_HANDLE_T = c_ulonglong  # uint64

#! Type that holds device serial.
# typedef char UNICORN_DEVICE_SERIAL[UNICORN_SERIAL_LENGTH_MAX];
UNICORN_DEVICE_SERIAL_T = c_char * UNICORN_SERIAL_LENGTH_MAX

#! Type that holds device version.
# typedef char UNICORN_DEVICE_VERSION[UNICORN_DEVICE_VERSION_LENGTH_MAX];
UNICORN_DEVICE_VERSION_T = c_char * UNICORN_DEVICE_VERSION_LENGTH_MAX

#! Type that holds firmware version.
# typedef char UNICORN_FIRMWARE_VERSION[UNICORN_FIRMWARE_VERSION_LENGTH_MAX];
UNICORN_FIRMWARE_VERSION_T = c_char * UNICORN_FIRMWARE_VERSION_LENGTH_MAX


# ========================================================================================
# Structures
# ========================================================================================

#! The type containing information about a single channel of the amplifier.
# typedef struct _UNICORN_AMPLIFIER_CHANNEL
# {
# 	#! The channel name.
# 	char name[32];
# 	#! The channel unit.
# 	char unit[32];
# 	#! The channel range as float array. First entry min value; Second max value.
# 	float range[2];
# 	#! The channel enabled flag. \ref TRUE to enable channel; \ref FALSE to disable channel.
# 	BOOL enabled;
# } UNICORN_AMPLIFIER_CHANNEL;
class UNICORN_AMPLIFIER_CHANNEL_T(Structure):
    _fields_ = [
        ("name", c_char*32),
        ("unit", c_char*32),
        ("range", c_float*2),
        ("enabled", c_bool),
    ]


#! The type holding an amplifier configuration.
# typedef struct _UNICORN_AMPLIFIER_CONFIGURATION
# {
# 	#! The array holding a configuration for each available \ref UNICORN_AMPLIFIER_CHANNEL.
# 	UNICORN_AMPLIFIER_CHANNEL Channels[UNICORN_TOTAL_CHANNELS_COUNT];
# } UNICORN_AMPLIFIER_CONFIGURATION;
class UNICORN_AMPLIFIER_CONFIGURATION_T(Structure):
    _fields_ = [
        ("Channels", UNICORN_AMPLIFIER_CHANNEL_T * UNICORN_TOTAL_CHANNELS_COUNT)
    ]

#! Type that holds additional information about the device.
# typedef struct _UNICORN_DEVICE_INFORMATION
# {
# 	#! The number of EEG channels.
# 	uint16_t numberOfEegChannels;
# 	#! The serial number of the device.
# 	UNICORN_DEVICE_SERIAL serial;
# 	#! The firmware version number.
# 	UNICORN_FIRMWARE_VERSION firmwareVersion;
# 	#!The device version number.
# 	UNICORN_DEVICE_VERSION deviceVersion;
# 	#! The PCB version number.
# 	uint8_t pcbVersion[4];
# 	#! The enclosure version number.
# 	uint8_t enclosureVersion[4];
# } UNICORN_DEVICE_INFORMATION;
class UNICORN_DEVICE_INFORMATION_T(Structure):
    _fields_ = [
        ("numberOfEegChannels", c_uint16),
        ("serial", UNICORN_DEVICE_SERIAL_T),
        ("firmwareVersion", UNICORN_FIRMWARE_VERSION_T),
        ("deviceVersion", UNICORN_DEVICE_VERSION_T),
        ("pcbVersion", c_uint8 * 4),
        ("enclosureVersion", c_uint8 * 4),
    ]

#! The type that holds information about the Bluetooth adapter
# typedef struct _UNICORN_BLUETOOTH_ADAPTER_INFO
# {
# 	#! The name of the Bluetooth adapter used.
# 	char name[UNICORN_STRING_LENGTH_MAX];
# 	#! The manufacturer of the Bluetooth adapter.
# 	char manufacturer[UNICORN_STRING_LENGTH_MAX];
# 	#! Indicating if the used Bluetooth adapter is a recommended (delivered) device. 
# 	#! \ref FALSE if the adapter is not a recommended device.
# 	#! \ref TRUE if the adapter is a recommended device.
# 	BOOL isRecommendedDevice;
# 	#! Indicates whether the Bluetooth adapter has reported a problem or not.
# 	#! \ref FALSE if the adapter behaves as supposed.
# 	#! \ref TRUE if the adapter reported a problem.
# 	BOOL hasProblem;
# } UNICORN_BLUETOOTH_ADAPTER_INFO;
class UNICORN_BLUETOOTH_ADAPTER_INFO_T(Structure):
    _fields_ = [
        ("name", c_char * UNICORN_STRING_LENGTH_MAX),
        ("manufacturer", c_char * UNICORN_STRING_LENGTH_MAX),
        ("isRecommendedDevice", c_bool),
        ("hasProblem", c_bool),
    ]

