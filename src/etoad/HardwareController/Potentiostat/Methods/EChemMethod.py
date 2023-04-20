from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Optional, Callable, Tuple, Union, List
import numpy as np
from ..BioLogic import TECH_ID, PROG_STATE, CurrentValues, DataInfo, DataBuffer
from etoad.Utils import ConfigLoader


class EChemMethod(metaclass=ABCMeta):
    """
    Abstract base class for electrochemical methods to be run on the Bio-Logic Instrument using the Python Interface.

    Public methods:
        __str__()
        method_file() -> str: Returns the path to the ecc file for the specific method.
        load_parameters(set_parameters: dict) -> list: Merges user-defined parameters into default configuration
        extract_data(data: tuple, numeric_to_single: Callable) -> tuple: Extracts results from the raw loaded data.
        process_data(extracted_data: np.ndarray) -> np.ndarray: Processes the full measurement dataset.

    Abstract attributes (need to be defined in "child" classes):
        method_name (str): Name of the experimental method
        method_name_short (str): Short form of the method name
        method_file_name (str): Name of the ecc file.
        data_structure (tuple): Tuple of column headers of the final data structure.

    Abstract methods (need to be defined in "child" classes):
        _decode_row(row: tuple, timebase: float, numeric_to_single: Callable) -> np.array: Decoder for raw data points.
        [OPTIONAL] process_data(extracted_data: np.ndarray) -> np.ndarray: Processes the full measurement dataset

    Each child class requires an additional config file containing the default settings for the respective method
    located in the same folder: $method_name_short$_Defaults.json
    """
    method_name: str = ""
    method_name_short: str = ""
    method_file_name: str = ""
    data_structure: tuple = ()

    def __init__(
            self,
            path_to_binaries: Path
    ):
        self.method = path_to_binaries / self.method_file_name

    def __str__(
            self
    ) -> str:
        return f"{self.method_name} ({self.method_name_short})"

    def method_file(
            self
    ) -> str:
        """
        Returns the absolute path to the method file as a string.

        Returns:
            String of the absolute path to the method file
        """
        return str(self.method)

    def load_technique_parameters(
            self,
            set_parameters: dict
    ) -> List[List[tuple]]:
        """
        Takes a dictionary of set parameters (key-value pairs, where the keys can either be the variable description
        or the parameter name, as required for the DLL function) and generates the list of arguments for the DLL
        function to define the parameter objects.

        Args:
            set_parameters: Dictionary of parameters set by the user.

        Returns:
            list: List of lists of parameters per iteration
        """
        config: dict = self._get_config(set_parameters)
        technique_parameters: dict = config["TechniqueParameters"]
        iteration_settings: dict = config["IterationSettings"]

        parameters_per_iteration: list = list()
        for iteration_num in range(iteration_settings["no_iterations"]):
            parameters_per_iteration.append(self._parse_parameters(technique_parameters, iteration_num))

        return parameters_per_iteration

    def _parse_parameters(
            self,
            technique_parameters: dict,
            iteration_num: int
    ) -> List[tuple]:
        """
        Parses the parameters (as passed through the dictionary) as a list of tuples (as required as args
        for the DLL functions).

        Args:
            technique_parameters: Dictionary of parameter names and specifications (as given in the json file).
            iteration_num: Index of the iteration.
        Returns:
            all_parameters: List of parameters, each one parsed as a tuple (as required for the DLL function).
        """
        all_parameters: list = []

        for parameter_details in technique_parameters.values():
            if parameter_details["changed_over_iterations"] is True:
                all_parameters.extend(self._parse_single_parameter(parameter_details["value"][iteration_num], parameter_details))
            else:
                all_parameters.extend(self._parse_single_parameter(parameter_details["value"], parameter_details))

        return all_parameters

    def _parse_single_parameter(
            self,
            value: Union[list, str, bool, float, int],
            parameter_details: dict
    ) -> List[tuple]:
        """
        Parses a single parameter by validating its parameter values and details.
        If the parameter is passed as a list (i.e. multiple values for a single measurement), each value is parsed
        individually.

        Args:
            value: Value of the parameter to be parsed.
            parameter_details: Dictionary of parameter details, as read in from the config.

        Returns:
            list: List of tuple(s), each value parsed as a tuple for the DLL function to be read in.
        """
        parsed_parameter: list = list()

        if type(value) is list:
            for i, single_value in enumerate(value):
                args: tuple = self._validate_parameter(
                    name=parameter_details["name"],
                    variable_type=parameter_details["variable_type"],
                    value=single_value,
                    constraints=parameter_details["constraints"],
                    index=i
                )
                parsed_parameter.append(args)

        else:
            args: tuple = self._validate_parameter(
                name=parameter_details["name"],
                variable_type=parameter_details["variable_type"],
                value=value,
                constraints=parameter_details["constraints"]
            )
            parsed_parameter.append(args)

        return parsed_parameter

    @staticmethod
    def _validate_parameter(
            name: str,
            variable_type: str,
            value: Union[int, float, bool],
            constraints: Union[None, str],
            index: Optional[Union[int, None]] = None
    ) -> tuple:
        """
        Parses the parameters, as given in the settings dictionary, into an args tuple (required by the DLL Function).
        (name[str], type[type], value[int, float, bool], index[Optional: int])
        Validates the passed data types and checks for constraint violation.

        Args:
            name: Name of the parameter, as required by the DLL function.
            variable_type: Python type of the parameter, given as a string (as read from the settings json file).
            value: Value of the parameter
            constraints: Constraint on the parameter values, given as a string (as read from the settings json file)
            index: Optional, integer index if a variable is to be declared multiple times.

        Returns:
            Tuple of the parameter settings, as required by the DLL function

        Raises:
            TypeError (if parameter is not of the specified type)
            ValueError (if parameter value violates the constraints)
        """
        parameter_type: type = eval(variable_type)

        if not type(value) is parameter_type:
            if type(value) in (int, float) and parameter_type in (int, float):
                value = parameter_type(value)
            else:
                raise TypeError("The passed value does not match the parameter type signature.")

        if constraints:
            if not eval(constraints, {"range": range}, {"x": value}):
                raise ValueError(f"The value {value} violates the constraint {constraints} for the parameter {name}.")

        if not index:
            return name, parameter_type, value
        else:
            return name, parameter_type, value, index

    def _get_config(
            self,
            set_parameters: dict
    ) -> dict:
        """
        Updates the default configuration dictionary by the key-value pairs passed as parameters.
        Keys can be either the variable description or the variable name as required by the DLL function.

        Args:
            set_parameters: Dictionary of parameters to override the default settings

        Returns:
            parameters_updated: Updated parameter dictionary.

        Raises:
            KeyError (if the key in parameters_set is not found in the default config).
        """
        parameters: dict = self._load_default_config()

        if "TechniqueParameters" not in set_parameters:
            return parameters

        if "IterationSettings" in set_parameters:
            parameters["IterationSettings"] = set_parameters["IterationSettings"]

        # ATTN: This is a bit lengthy – maybe there is a good way around that here, where we still allow for
        #       setting parameters both by dictionary key and by parameter name
        for key in set_parameters["TechniqueParameters"]:
            key_found: bool = False
            if key in parameters["TechniqueParameters"]:
                parameters["TechniqueParameters"][key]["value"] = set_parameters["TechniqueParameters"][key]["value"]
                parameters["TechniqueParameters"][key]["changed_over_iterations"] = False if "changed_over_iterations" not in set_parameters["TechniqueParameters"][key] else set_parameters["TechniqueParameters"][key]["changed_over_iterations"]
                key_found = True
            else:
                for param in parameters["TechniqueParameters"]:
                    if key == parameters["TechniqueParameters"][param]["name"]:
                        parameters["TechniqueParameters"][param]["value"] = set_parameters["TechniqueParameters"][key]["value"]
                        parameters["TechniqueParameters"][param]["changed_over_iterations"] = False if "changed_over_iterations" not in set_parameters["TechniqueParameters"][key] else set_parameters["TechniqueParameters"][key]["changed_over_iterations"]
                        key_found = True

            if not key_found:
                raise KeyError(f"{key} was not found in the default settings for {self.method_name_short}.")

        return parameters

    def _load_default_config(
            self
    ) -> dict:
        """
        Loads the default parameters from the $METHOD_Defaults.json located in the same folder
        and returns the dictionary:

        Returns:
            Dictionary of default settings.
        """
        default_file: Path = Path(__file__).parent / f"{self.method_name_short}_Defaults.json"
        return ConfigLoader.load_config(default_file)

    def extract_data(
            self,
            data: Tuple[CurrentValues, DataInfo, DataBuffer],
            numeric_to_single: Optional[Callable]
    ) -> Tuple[np.ndarray, dict]:
        """
        Public method to decode the experimentally recorded data into a numpy ndarray.

        Args:
            data: Tuple of data recorded from the API (ata architectures to receive the DLL method returns).
            numeric_to_single: Function that can convert a numeric value to a 32-bit value (from the API).

        Returns:
            extracted_data: Numpy ndarray of all experimental data extracted.
            metadata: Dictionary of experiment metadata.
        """
        current_values, data_info, data_record = data
        metadata: dict = self._unpack_metadata(current_values, data_info)
        extracted_data: np.ndarray = np.array([])

        start_index = 0
        for _ in range(data_info.NbRows):
            row: tuple = data_record[start_index: start_index + data_info.NbCols]
            extracted_row: np.array = self._decode_row(row, metadata["timebase"], numeric_to_single)
            extracted_data = self._merge_data(extracted_data, extracted_row)
            start_index = start_index + data_info.NbCols

        return extracted_data, metadata

    @staticmethod
    def _unpack_metadata(
            current_values: CurrentValues,
            data_info: DataInfo
    ) -> dict:
        """
        Extracts the metadata from the experimentally recorded data.

        Args:
            current_values: CurrentValues object, as required by the DLL function
            data_info: DataInfo object, as required by the DLL function

        Returns:
            metadata: Dictionary of measurement metadata
        """
        status = PROG_STATE(current_values.State).name
        technique_name = TECH_ID(data_info.TechniqueID).name

        metadata = {
            "timebase": current_values.TimeBase,
            "index": data_info.TechniqueIndex,
            "technique": technique_name,
            "process_index": data_info.ProcessIndex,
            "loop": data_info.loop,
            "skip": data_info.IRQskipped,
            "status": status
        }

        return metadata

    @staticmethod
    @abstractmethod
    def _decode_row(
            row: tuple,
            timebase: float,
            numeric_to_single: Optional[Callable]
    ) -> np.array:
        """
        Method to decode a single row of experimental data recorded experimentally.

        Args:
            row: Tuple of values as extracted from output of the DLL functions.
            timebase: Current time base step, as extracted from the metadata
            numeric_to_single: Function that can convert a numeric value to a 32-bit value (from the API).
        """
        raise NotImplementedError

    def process_data(
            self,
            extracted_data: np.ndarray
    ) -> np.ndarray:
        """
        Specific processing method for the data returned from a specific measurement technique
        (e.g. calculation of differential spectra for pulsed techniques).

        Returns the unprocessed data, if not declared for a specific child class.
        """
        return extracted_data

    @staticmethod
    def _merge_data(
            original_data: np.ndarray,
            new_data: np.array
    ) -> np.ndarray:
        """
        Merges a new 1D numpy array (new_data) into a 2D array (original_data) by appending it along axis 0.
        If the original_data array is empty, a new 2D array of correct dimensionality is generated from new_data.

        Args:
            original_data: 2D Numpy ndarray
            new_data: 1D Numpy array to be appended to original_data

        Returns:
            2D Numpy array as a merger from original_data and new_data.
        """
        if original_data.size != 0:
            return np.append(original_data, [new_data], axis=0)
        else:
            return np.array([new_data])
