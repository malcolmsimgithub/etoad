from math import log2
from sys import maxsize


def get_bit_mode() -> int:
    """
    Determines the bit mode of the Python installation (32 / 64) in the OS.
    Checks for the maximum integer and takes the log2 to determine the bit mode.

    Returns:
        n_bits: Integer of the bit mode.

    Raises:
        ValueError: System is not a 32- or 64-bit system.
    """
    n_bits: int = round(log2(maxsize) + 1)

    if n_bits in (32, 64):
        return n_bits

    raise ValueError("The System Bit Mode is neither 32-bit nor 64-bit!")
