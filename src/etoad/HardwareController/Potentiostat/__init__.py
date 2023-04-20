"""
Interface to the Bio-Logic Potentiostat for Electrochemical Measurements.

General Workflow:
    1. Install and connect all electrodes in the measurement cell.
    2. Switch on the Potentiostat (takes approx. 30 s to establish connection to the PC).
    3. Open the EC-Lab Express Software and establish a connection to the instrument (load general firmware).
    4. You're now ready to control the potentiostat via this package and an EChemController object (API Doc below).

Main Controller Class: EChemController

Public Methods:

    __init__(
        config_path: Path -> Path to the potentiostat configuration file (json dictionary).
        logger: Logger -> Logger object (from the logging package) to document all experiments.

    load_technique(
        technique: str -> Name of the measurement technique
        set_parameters: dict -> Parameters (name or identifier : value) that deviate from the default settings.
        channel: int -> Optional: Number of the channel to load the method to (starting from 1).
    ) -> None

    do_measurement(
        channel: int -> Optional: Number of the channel to run the experiment (starting from 1).
    ) -> np.ndarray of all collected experimental results.
"""

from .EChemController import EChemController
