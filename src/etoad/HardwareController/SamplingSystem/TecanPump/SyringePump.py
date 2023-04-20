__author__ = "Tony C. Wu (@verysure), Felix Strieth-Kalthoff (@felix-s-k)"


import time
from abc import ABCMeta, abstractmethod
from typing import Union, Optional


class SyringePump(metaclass=ABCMeta):
    """
    Abstract Base Class for handling different kinds of syringe pumps.
    """
    syringe_volume: Optional[float] = None

    # Public Methods for Using the Syringe Pump

    def draw(self, volume: float, valve_port: Optional[Union[int, str]] = None) -> None:
        """
        Draws a specific volume through a given valve port.

        Args:
            volume: Volume to draw (in mL).
            valve_port: Identifier of the valve port to be used.
        """
        if valve_port is not None:
            valve_port: int = self._convert_port(valve_port)
            self._set_valve(valve_port)
        if volume > 0:
            piston_position: int = self._get_position() + int(volume / self.syringe_volume * self._get_max_steps())
            self._set_position(piston_position)

    def dispense(self, volume: float, valve_port: Optional[Union[int, str]] = None) -> None:
        """
        Dispenses a specific volume through a given valve port.

        Args:
            volume: Volume to draw (in mL).
            valve_port: Identifier of the valve port to be used.
        """
        if valve_port is not None:
            valve_port: int = self._convert_port(valve_port)
            self._set_valve(valve_port)
        if volume > 0:
            piston_position: int = self._get_position() - int(volume / self.syringe_volume * self._get_max_steps())
            self._set_position(piston_position)

    def draw_and_dispense(
            self,
            draw_valve_port: Union[int, str],
            dispense_valve_port: Union[int, str],
            volume: float,
            wait: Optional[float] = None,
            velocity: Optional[float] = None
    ) -> None:
        """
        Draws a specified amount of volume from a specified port, and dispenses it to a specified port.
        Can temporarily change the draw/dispense velocity, if specified.

        Args:
             draw_valve_port: Identifier of the valve port to be used for drawing liquid.
             dispense_valve_port: Identifier of the valve port to be used for dispensing liquid.
             volume: Volume to be drawn and dispensed (in mL).
             wait: Waiting time between draw and dispense (in sec).
             velocity: Draw / dispense velocity to be set temporarily(if differing from the default value).

        """
        draw_valve_port: int = self._convert_port(draw_valve_port)
        dispense_valve_port: int = self._convert_port(dispense_valve_port)

        if velocity:
            old_velocity: float = self.get_velocity()
            self.set_velocity(velocity)

        # Multiple aspirations, if the dispense volume is greater than the syringe volume
        while volume >= self.syringe_volume:
            volume -= self.syringe_volume
            self._draw_full(draw_valve_port)
            if wait:
                time.sleep(wait)
            self._dispense_all(dispense_valve_port)

        self.draw(volume, draw_valve_port)
        if wait:
            time.sleep(wait)
        self._dispense_all(dispense_valve_port)

        if velocity:
            self.set_velocity(old_velocity)

    # Private Methods -> Valve Position

    @abstractmethod
    def _set_valve(self, valve_position: int) -> None:
        """
        Abstract method for setting the valve to a specified port.

        Args:
            valve_position: Integer value of the valve position.
        """
        raise NotImplementedError

    @abstractmethod
    def _get_position(self) -> int:
        """
        Abstract method that reads the current valve position.

        Returns:
            int: Current valve position.
        """
        raise NotImplementedError

    def _convert_port(self, port: Union[str, int]) -> int:
        """
        If applicable, converts the human identifier for a port (as key in the ports attribute) to the respective
        computer identifier.

        Args:
            port: Human identifier for the port.

        Returns:
            int: Port number, as required for communication with the pump.
        """
        if isinstance(port, str):
            port = self.ports.get(port)
        if port is not None:
            return port
        else:
            raise ValueError('Wrong ports')

    # Private Methods -> Piston Movement and Position

    @abstractmethod
    def _set_position(self, piston_position: int) -> None:
        """
        Abstract method that sets the piston to a specific position.

        Args:
            piston_position: Integer value of the target piston position
        """
        raise NotImplementedError

    @abstractmethod
    def _get_max_steps(self) -> int:
        """
        Abstract method to get the maximum number of steps from the pump.

        Returns:
            int: Maximum number of piston steps.
        """
        raise NotImplementedError

    def _draw_full(self, valve_port: Optional[Union[int, str]] = None) -> None:
        """
        Fills the complete syringe through a given valve port.

        Args:
            valve_port: Identifier of the valve port to be used.
        """
        if valve_port is not None:
            valve_port: int = self._convert_port(valve_port)
            self._set_valve(valve_port)
        self._set_position(self._get_max_steps())

    def _dispense_all(self, valve_port: Optional[Union[int, str]] = None) -> None:
        """
        Dispenses the entire syringe volume through a given port.

        Args:
            valve_port: Identifier of the valve port to be used.
        """
        if valve_port is not None:
            valve_port: int = self._convert_port(valve_port)
            self._set_valve(valve_port)
        self._set_position(0)

    def __getattr__(self, attr):
        if attr in self.info:
            return self.info[attr]
        else:
            raise ValueError(f'{attr} no exist in obj or obj.info')


