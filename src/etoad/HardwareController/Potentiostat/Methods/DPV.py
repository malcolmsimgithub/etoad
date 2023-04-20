from typing import Optional, Callable
import numpy as np
from .EChemMethod import EChemMethod


class DPV(EChemMethod):
    """
    Implementation of the Differential Pulse Voltammetry Method.
    """
    method_name: str = "Differential Pulse Voltammetry"
    method_name_short: str = "DPV"
    method_file_name: str = "dpv4.ecc"
    data_structure: tuple = ("Time", "Voltage", "Current")

    @staticmethod
    def _decode_row(row: tuple, timebase: float, numeric_to_single: Optional[Callable]) -> np.array:
        """
        SWV-Specific implementation of decoding a single row of experimental results:

        Args:
            row: Tuple of values parsed from the experimental data
            timebase: Current time base step, as extracted from the metadata.
            numeric_to_single: Function to convert C++ signature numericals to singles.
        """
        time_high, time_low, voltage, current = row

        time = timebase * ((time_high << 32) + time_low)
        current = numeric_to_single(current)
        voltage = numeric_to_single(voltage)

        return np.asarray([time, voltage, current])

    def process_data(self, extracted_data: np.ndarray) -> np.ndarray:
        """
        Processes the full extracted dataset by generating the differential voltammogram.
        Generates the current difference from the two data points of a pulse (posterior - prior).

        Args:
            extracted_data: 2D Numpy array of all measured data points.

        Returns:
            processed_data: 2D Numpy array of all pulse data points.

        """
        pulse_high: np.array = extracted_data[:, 2][0::2]
        pulse_low: np.array = extracted_data[:, 2][1::2]
        no_data_points: int = pulse_low.shape[0]

        # in rare cases, it happens that the total number of data points extracted from the channel is odd...
        if not pulse_high.shape[0] == no_data_points:
            pulse_high = pulse_high[:no_data_points]

        differential_current: np.array = pulse_high - pulse_low

        processed_data: np.ndarray = np.vstack(
            (
                extracted_data[:, 0][0::2][:no_data_points],    # Time from Column 0
                extracted_data[:, 1][0::2][:no_data_points],    # Voltage from Column 1
                differential_current                            # Differential Current from Column 2
            )
        )

        return processed_data.transpose()
