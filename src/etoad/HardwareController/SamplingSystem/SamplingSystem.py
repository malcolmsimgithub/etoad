import time
from pathlib import Path
from typing import Union
from logging import Logger

from .TecanPump import TecanPump
from .AtmosphereHandler import AtmosphereHandler
from etoad.Utils import ConfigLoader


class SamplingSystem:
    """
    Simple System for Sampling Liquids into a Measurement Cell using a Tecan Syringe Pump (Driver by Tony Wu).
    Current implementation only works for a system with a single multi-port syringe pump.

    Public Methods to be called from external:
        transfer_to_cell(source_port: int, volume: float) -> None
        dilute_cell(volume: float = 0, factor: float = 1) -> None
        purge_cell(purge_time: int = 10) -> None
        wash_cell(volume: float, cycles: int = 3) -> None
    """

    # TODO [at some point...]: Dead volume handling in the valve / syringe
    # For now, dead volume upon transferring small sample quantities can be dealt with by doing the sample transfer
    # first, and the dilution step later, so that all dead volume of sample is subsequently passed to the same
    # vessel as the sample. But that's not a generalizable solution...

    required_settings: set = {
        "visa_address",
        "device_address",
        "pump_volume",
        "initial_valve",
        "default_velocity",
        "dead_volume",
        "cell_port",
        "wash_port",
        "waste_port",
        "relay_settings"
    }

    defined_ports: set = {
        "cell_port",
        "wash_port",
        "waste_port"
    }

    def __init__(self, config_file: Path, logger: Logger, initial_wash: int = 1, cell_filled: bool = True):
        """
        Creates an instance of the SamplingSystem class.

        Args:
            config_file: Path to the configuration file. Needs to contain the specified keys in self.required_settings.
            logger: Logger object
            initial_wash: Number of initial washing steps. Default: 3  # TODO: Refactor to pump_wash or a similar name to not confuse it with cell_wash
        """

        self._config: dict = ConfigLoader.load_config(config_file, self.required_settings)

        self._atmosphere_handler: AtmosphereHandler = AtmosphereHandler(**self._config["relay_settings"])

        self._logger: Logger = logger

        self._pump: Union[XCPump, None] = None
        self.cell_port: Union[int, None] = None

        self.wash_port: Union[int, None] = None
        self.waste_port: Union[int, None] = None

        self._set_ports()
        self._initialize_pump(initial_wash)

        if cell_filled:
            self._cell_volume: float = 5.0
            self._empty_cell()
        else:
            self._cell_volume: float = 0

        self._logger.info("Autosampler and inert gas handling were successfully initialized. ")

    def _initialize_pump(self, initial_wash: int = 3) -> None:
        """
        Creates an instance of the XCPump, sets the velocity and primes the pump.
        """
        self._pump: TecanPump = TecanPump(
            visa_address=self._config["visa_address"],
            device_address=self._config["device_address"],
            init_valve=self._config["initial_valve"],
            syringe_volume=self._config["pump_volume"],
        )

        self._pump.set_velocity(self._config["default_velocity"])

        self._wash_pump(initial_wash)

    def _set_ports(self) -> None:
        """
        Sets the special ports "_cell_port", "wash_port" and "waste_port" as attributes of the class.
        """
        for port in self.defined_ports:
            setattr(self, port, self._config[port])

    def transfer_to_cell(self, source_port: int, volume: float, wash_line: bool = False) -> None:
        """
        Transfers a given amount of liquid to the measurement cell.

        Args:
            source_port: Port from which the liquid should be moved to the cell.
            volume: Volume to be dispensed
            wash_line: Whether to wash the line to remove contaminations, e.g. from previous samples.
        """
        if wash_line:
            self._pump.draw_and_dispense(source_port, self.waste_port, self._config["dead_volume"], wait=1)
            self._wash_pump(1)

        self._pump.draw_and_dispense(source_port, self.cell_port, volume + self._config["dead_volume"], wait=2)
        self._update_cell_volume(volume)

    def dilute_cell(self, volume: float = 0, factor: float = 1) -> None:
        """
        Dilutes the solution in the cell based on either a fixed volume or a dilution factor.

        Args:
            volume: Volume of the wash solution (in mL) to be added. If given, the dilution factor is ignored.
            factor: Dilution factor.
        """
        if volume == 0:
            volume = self._cell_volume * (factor - 1)

        self.transfer_to_cell(self.wash_port, volume)

    def purge_cell(self, purge_time: float = 10) -> None:
        """
        Purges the cell with inert gas.

        Args:
            purge_time: Purge time (in seconds).
        """
        with self._atmosphere_handler.open_atmosphere():
            time.sleep(purge_time)

        self._logger.debug(f"Cell was purged with Nitrogen gas for {purge_time} sec.")

    def _wash_pump(self, cycles=3):
        """
        Washes the syringe pump for three times with its volume of wash liquid.
        """
        for _ in range(cycles):
            self._pump.draw_and_dispense(self.wash_port, self.waste_port, self._config["pump_volume"], wait=1)

    def wash_autosampler_position(self, sampler_position: int, no_cycles: int = 3) -> None:
        """
        Discards a sample in the autosampler and washes the vial.

        Args:
            sampler_position: Source port of the sample vial that should be cleaned.
            no_cycles: Number of wash cycles.
        """
        self._pump.draw_and_dispense(sampler_position, self.waste_port, 7.5, wait=1)
        self._wash_pump(1)
        for _ in range(no_cycles):
            self._pump.draw_and_dispense(self.wash_port, sampler_position, 5)
            self._pump.draw_and_dispense(sampler_position, self.waste_port, 6)

    def wash_cell(self, wash_volume: float, cycles=3) -> None:
        """
        Washes the cell for n times:
            - first time: 15 mL of wash solution to wash off also the sides of the measurement cell
            - other n-1 times: given volume of the wash solution.
        """
        self._empty_cell()

        self.transfer_to_cell(self.wash_port, 15)
        time.sleep(5)
        self._empty_cell()

        for _ in range(cycles-1):
            self.transfer_to_cell(self.wash_port, wash_volume)
            time.sleep(5)
            self._empty_cell()

        self._logger.debug("Measurement Cell was successfully emptied and washed.")

    def _empty_cell(self):
        """
        Removes the entire amount of liquid from the cell.
        """
        with self._atmosphere_handler.open_atmosphere():
            self._pump.draw_and_dispense(self.cell_port, self.waste_port, self._cell_volume + 2, wait=1)
            self._update_cell_volume(-self._cell_volume)

    def _update_cell_volume(self, volume: float) -> None:
        """
        Updates the cell volume based on the volume transferred to / from the cell.

        Args:
            volume: Volume added to (positive) / removed from (negative) the cell.
        """
        self._cell_volume += volume

    def disconnect(self) -> None:
        """
        Closes the connection to the pump by closing the pyvisa resource manager.
        """
        self._pump.manager.close()
        self._logger.info("Connection to the sampling system was successfully closed.")




