#!/usr/bin/env python
__author__ = 'Felix Strieth-Kalthoff'

from array import array
from contextlib import contextmanager
from pathlib import Path
from typing import Union, List
import numpy as np

from etoad.Utils import ConfigLoader
from etoad.Interface import GraphicalInterface
from .Binaries import BINARY_PATH
from ..Potentiostat import BioLogic as KBIO
from .DataStructures import *
from .Methods import *
from .DLL_Binding import EClibDLLInterface


class EChemController(object):
    """
    Minimalistic API-type Interface to the Bio-Logic Potentiostats.

    Public Methods:
        load_technique(technique: str, set_parameters: dict)
        do_measurement(channel: int)
        stop_channel(channel: int)
        disconnect()
    """

    required_settings: set = {
        "port",
        "channel_ids",
        "default_channel_id",
        "timeout",
        "plot_in_real_time"
    }

    def __init__(
            self,
            config_file: Path,
            logger: GraphicalInterface,
            simulation_mode: bool = False
    ):
        """
        Instantiates an API-type interface to the Bio-Logic Potentiostats.

        Sets the following attributes:
            self.binary_path: Path to the directory where the binaries are located.
            self._dll_functions: Callable DLL interface to execute the DLL methods.
            self.device_id: ID of the connected potentiostat device.
            self.channel: Number of the channel (counting from 0)
            self.technique: Class describing the experimental technique (inherited from EChemMethod).
        """
        self.binary_path: Path = BINARY_PATH
        self._dll_functions: EClibDLLInterface = EClibDLLInterface(self.binary_path, logger, simulation_mode)

        self.config: dict = ConfigLoader.load_config(config_file, self.required_settings)
        self.logger: GraphicalInterface = logger

        self._simulation: bool = simulation_mode

        self.default_channel: int = self.config["default_channel_id"]
        self.device_id: int = self._connect()

        self.technique: Union[EChemMethod, None] = None

    def _connect(
            self,
    ) -> int:
        """
        Sets up the potentiostat device.
            1. Establishes the connection to the device.
            2. Loads the firmware to the channels.
            3. Checks for functionality of all channels.

        Returns:
            device_id.value: Integer value of the device ID

        Raises:
            ConnectionError (if connection to the channels could not be established)
        """
        # Establish connection to the device (-> BL_Connect)
        port: str = self.config["port"]
        timeout: int = self.config["timeout"]
        device_id, device_info = c_int32(), KBIO.DeviceInfo()
        self._dll_functions("BL_Connect", port.encode(), timeout, device_id, device_info)
        self.logger.debug(device_info)

        # Load Firmware to all channels specified in the config (BL_LoadFirmware)
        # ATTN: Had problems with this before -> copying the original xlx and bin files to the binaries folder helped...
        channels_array = KBIO.ChannelsArray()
        for channel in self.config["channel_ids"]:
            channels_array[channel] = c_bool(True)
        results_array = KBIO.ResultsArray()
        self._dll_functions(
            "BL_LoadFirmware",
            device_id.value,
            channels_array,
            results_array,
            KBIO.MAX_SLOT_NB,
            False,
            False,
            self._dll_functions.get_firmware_file("bin").encode(),
            self._dll_functions.get_firmware_file("xlx").encode()
        )

        # Check if firmware was loaded and channel is ready (BL_GetChannelInfos)
        for channel in self.config["channel_ids"]:

            channel_info = KBIO.ChannelInfo()
            self._dll_functions("BL_GetChannelInfos", device_id.value, channel, channel_info)
            self.logger.debug(channel_info)

            if not channel_info.is_kernel_loaded and not self._simulation:
                self.logger.error(
                    f"Channel {channel + 1} was not successfully loaded. No measurement can be performed.")
                raise ConnectionError("The connection to the instrument could not be established.")

        self.logger.info(f"Connection to the Potentiostat on {port} successfully established.")

        return device_id.value

    def disconnect(
            self
    ) -> None:
        """
        Disconnects the potentiostat.
        """
        self._dll_functions("BL_Disconnect", self.device_id)
        self.logger.info("Connection to the potentiostat was successfully closed.")

    #################################################################
    # METHODS RELATED TO LOADING TECHNIQUES AND DEFINING PARAMETERS #
    #################################################################

    def _load_technique_to_channel(
            self,
            parameters_list: List[tuple],
            channel: Union[int, None] = None
    ) -> None:
        """
        Public Method.
        Sets the passed experimental technique to be used, loads and parses all experimental parameters.

        Args:
            parameters_list: list of parameters as arguments for the DLL function for setting parameter objects
            channel: ID of the channel that the technique should be loaded to.
        """
        parameters_processed: KBIO.EccParams = self._parse_measurement_parameters(parameters_list)

        self._dll_functions(
            "BL_LoadTechnique",
            self.device_id,
            channel,
            self.technique.method_file().encode(),
            parameters_processed,
            True,  # True if it is the first technique loaded to the channel
            True,  # True if it is the last technique loaded to the channel
            False  # Checks whether a Tkinter window pops up for parameter confirmation - optional / verbosity?
        )

        self.logger.info(f"Method {self.technique} was successfully loaded to channel {channel + 1}.")

    def _get_technique(
            self,
            technique: str,
    ) -> EChemMethod:
        """
        Method for evaluating the passed technique name to instantiate an EChemMethod object.

        Args:
            technique: Name of the measurement technique

        Returns:
            the specific measurement type object (EChemMethod class).
        """
        return eval(technique)(self.binary_path)

    def _parse_measurement_parameters(
            self,
            parameters_list: list,
    ) -> KBIO.EccParams:
        """
        Processes the measurement parameters for a single measurement (one "iteration") by generating a single
        KBIO.EccParams object required for loading the method via the DLL.

        Args:
            parameters_list: list of parameters as arguments for the DLL function for setting parameter objects

        Returns:
            KBIO.EccParms: KBIO-specific object of all measurement parameters.
        """
        parameter_objects = [self._dll_functions.define_parameter(*specification) for specification in parameters_list]

        no_params = len(parameter_objects)
        parameter_array = KBIO.ECC_PARM_ARRAY(no_params)

        for i, param_obj in enumerate(parameter_objects):
            parameter_array[i] = param_obj

        return KBIO.EccParams(no_params, parameter_array)

    ########################################################
    # METHODS RELATED TO ACTUALLY PERFORMING A MEASUREMENT #
    ########################################################

    def do_measurement(
            self,
            technique: str,
            set_parameters: dict,
            channel: Union[int, None] = None
    ) -> np.ndarray:
        """
        Main public method to run a measurement (possibly multiple iterations of a measurement).

        For each iteration, the following steps are performed:
            - parsing all technique parameters for that iteration
            - loading technique parameters to the channel
            - running the channel and recording the data

        Args:
            technique: String definition of the measurement technique to be used. Must match the class name.
            set_parameters: Dictionary of method parameters set/specified by the user
                            (Keys can be either parameter descriptions or parameter names)
            channel: ID of the channel that the technique should be loaded to.

        Returns:
            np.ndarray: 2D Numpy array (n_data_points, 4) of the results data
        """
        if not channel:
            channel = self.default_channel
        else:
            channel = channel - 1

        self.technique = self._get_technique(technique)
        parameters_per_iteration: List[List[tuple]] = self.technique.load_technique_parameters(set_parameters)

        results: np.ndarray = np.array([])
        self.logger.start_plotting(
            self.technique.method_name,
            self.technique.data_structure[1],
            self.technique.data_structure[2]
        )

        for iteration_num, iteration_params in enumerate(parameters_per_iteration):
            self._load_technique_to_channel(iteration_params, channel)
            iteration_results: np.ndarray = self._run_single_measurement(channel)
            iteration_results = np.hstack((iteration_results, np.full((iteration_results.shape[0], 1), iteration_num, dtype=int)))
            results = self._merge_data(results, iteration_results)

        return results

    def _run_single_measurement(
            self,
            channel: Union[int, None] = None
    ) -> np.ndarray:
        """
        Performs an actual measurement by starting the measurement on the channel and loading, unpacking and decoding
        the obtained data. Returns the measured data as a 2D Numpy array (method-specific format).

        Args:
            channel: Number of the channel to perform the measurement on.

        Returns:
            np.ndarray: 2D Numpy array of the results data

        Raises:
            ModuleNotFoundError (no technique loaded)
        """
        # Check for technique and channel information
        if not self.technique:
            raise ModuleNotFoundError("No Method has been loaded.")

        # Do the actual measurement
        results: np.ndarray = np.array([])
        with self._open_channel(channel):
            while True:
                try:
                    data: tuple = self._get_data(channel)
                    data_decoded, metadata = self.technique.extract_data(data, self._decode_numeric_to_single)
                    results = self._merge_data(results, data_decoded)

                    if np.any(results):
                        preprocessed_data = self.technique.process_data(results)
                        self.logger.update_plot(preprocessed_data[:, 1], preprocessed_data[:, 2])
                        # ATTN: This is currently hard-coded, assuming that the column structure is always the same

                except StopIteration:
                    if metadata["status"] == "STOP":
                        break
                    continue

                # Breaks the while loop upon keyboard interrupt - closes channel connection via context manager
                except KeyboardInterrupt:
                    self.logger.error("Measurement was interrupted through keyboard interrupt.")
                    break

        return self.technique.process_data(results)

    def _get_data(
            self,
            channel: int
    ) -> tuple:
        """
        Reads the data from the current channel, returns the metadata, current values, and all read-in data.

        Args:
            channel: ID of the channel to read the data from.

        Returns:
            current_values: CurrentValues object as a data infrastructure (save instrument state from DLL methods).
            data_info: DataInfo object as a data infrastructure to save method metadata from the DLL methods.
            data_buffer: Array of all read data.
        """
        data_buffer: KBIO.DataBuffer = KBIO.DataBuffer()
        data_info: KBIO.DataInfo = KBIO.DataInfo()
        current_values: KBIO.CurrentValues = KBIO.CurrentValues()

        self._dll_functions("BL_GetData", self.device_id, channel, data_buffer, data_info, current_values)

        rows: int = data_info.NbRows
        columns: int = data_info.NbCols
        data_buffer = array('L', data_buffer[:rows * columns])

        return current_values, data_info, data_buffer

    @staticmethod
    def _merge_data(
            old_data: np.ndarray,
            new_data: np.ndarray
    ) -> np.ndarray:
        """
        Appends a new ndarray to an existing ndarray using the numpy.append method.
        Returns the new array if the existing array is empty. Raises a StopIteration if the new array is empty.

        Args:
            old_data: Existing numpy ndarray
            new_data: Numpy ndarray to be appended

        Returns:
            Numpy ndarray as a merger of old and new array.

        Raises:
            StopIteration (if new_data is empty).
        """
        if old_data.size == 0:
            return new_data

        if new_data.size == 0:
            raise StopIteration

        return np.append(old_data, new_data, axis=0)

    def _start_channel(
            self,
            channel: int
    ) -> None:
        """
        Method to start a channel to begin a specific measurement.

        Args:
            channel: ID of the channel to start.
        """
        self._dll_functions("BL_StartChannel", self.device_id, channel)
        self.logger.info(f"Measurement of Technique {self.technique} started on channel {channel + 1}")

    def stop_channel(
            self,
            channel: int
    ) -> None:
        """
        Method to shut down a channel after completion of a measurement.

        Args:
            channel: ID of the channel to be stopped
        """
        self._dll_functions("BL_StopChannel", self.device_id, channel)
        self.logger.info(f"Connection to Channel {channel + 1} closed.")

    @contextmanager
    def _open_channel(
            self,
            channel: int
    ) -> None:
        """
        Context manager to open and close a specific channel for measurements.

        Args:
            channel: ID of the channel to be started and stopped
        """
        self._start_channel(channel)
        try:
            yield
        finally:
            self.stop_channel(channel)

    def _decode_numeric_to_single(
            self,
            raw_numeric: Union[str, int, float]
    ) -> float:
        """
        Method that uses the DLL to convert a raw numeric value into a single Python float.

        Returns:
            raw_numeric: Raw numerical value
        """
        result = c_float()
        self._dll_functions("BL_ConvertNumericIntoSingle", raw_numeric, result)
        return result.value
