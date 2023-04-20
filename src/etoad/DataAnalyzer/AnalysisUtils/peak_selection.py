from typing import List, Callable, Tuple


def filter_peaks(peak_list: List[dict], filters: list) -> List[dict]:
    """
    Filters a list of peak dictionaries by removing entries that do not fulfil the filtration criteria.

    Format for each filter:
        {
          "key": Name of the peak property to be filtered
          "operation": Evaluatable string representation of the operation to be performed (argument x).
        }

    Args:
        peak_list: List of peaks (each one given as a dictionary)
        filters: List of filter operations (each one of the format given above)

    Returns:
        peak_list: Filtered list of peaks
    """
    for filter in filters:
        filter_func: Callable = lambda x: eval(filter["operation"])
        peak_list = [peak for peak in peak_list if filter_func(peak[filter["key"]])]

    return peak_list


def select_peaks(peak_list: List[dict], operation: dict) -> Tuple[int, dict]:
    """
    Selects a peak from a given peak list based on a selection operation.

    Format for the operation:
        {
          "key": Name of the peak property to be evaluated
          "operation": Evaluatable string representation of the operation to be performed (argument x).
        }

    Args:
        peak_list: List of peaks (each one given as a dictionary)
        operation: Operation to perform peak selection (evaluatable string).

    Returns:
        peak: Selected peak as a dictionary
    """
    peak_properties = [peak[operation["key"]] for peak in peak_list]

    operation_func: Callable = lambda x: eval(operation["operation"])

    peak_idx: int = peak_properties.index(operation_func(peak_properties))

    return peak_idx, peak_list[peak_idx]
