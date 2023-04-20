from typing import Optional, Callable
import numpy as np
from .EChemMethod import EChemMethod


class OCV(EChemMethod):
    """
    Implementation of the Open Circuit Voltammetry.
    """
    method_name: str = "Open Circuit Voltammetry"
    method_name_short: str = "OCV"
    method_file_name: str = "ocv4.ecc"
    data_structure: tuple = ("Time", "Voltage")

    @staticmethod
    def _decode_row(row: tuple, timebase: float, numeric_to_single: Optional[Callable]) -> np.array:
        """
        CV-Specific implementation of decoding a single row of experimental results.

        Args:
            row: Tuple of values parsed from the experimental data
            timebase: Current time base step, as extracted from the metadata.
            numeric_to_single: Function to convert C++ signature numericals to singles.
        """
        time_high, time_low, voltage = row

        time = timebase * ((time_high << 32) + time_low)
        voltage = numeric_to_single(voltage)

        return np.asarray([time, voltage])
