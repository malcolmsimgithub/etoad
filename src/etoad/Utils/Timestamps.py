import time


def timestamp_date():
    """
    Get a timestamp string in the YYYY-MM-DD format.

    Returns:
        timestamp (str)
    """
    timestamp = time.strftime("%y-%m-%d", time.localtime())
    return timestamp


def timestamp_time():
    """
    Get a timestamp string in the HH-MM format.

    Returns:
        timestamp (str)
    """
    timestamp = time.strftime("%H-%M", time.localtime())
    return timestamp


def timestamp_time_precise():
    """
    Get a timestamp string in the HH-MM-SS format.

    Returns:
        timestamp (str)
    """
    timestamp = time.strftime("%H-%M-%S", time.localtime())
    return timestamp


def timestamp_datetime():
    """
    Get a timestamp string in the YYYY-MM-DD HH-MM format.

    Returns:
        timestamp (str)
    """
    timestamp = f"{timestamp_date()}_{timestamp_time()}"
    return timestamp


def timestamp_datetime_precise():
    """
    Get a timestamp string in the YYYY-MM-DD HH-MM-SS format.

    Returns:
        timestamp (str)
    """
    timestamp = f"{timestamp_date()}_{timestamp_time_precise()}"
    return timestamp
