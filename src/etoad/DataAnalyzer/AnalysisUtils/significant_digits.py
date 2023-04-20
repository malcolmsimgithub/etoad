import numpy as np
from typing import Union
from math import log10, floor


def significant_digits(number: Union[int, float, np.float64], no_digits: int = 3) -> float:
    """
    Returns a value with the given number of significant figures.

    Args:
        number: Value to be rounded
        no_digits: Number of significant figures.
    """
    no_decimal_places = -int(floor(log10(abs(number)))) + no_digits - 1
    return float(round(number, no_decimal_places))