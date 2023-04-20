import numpy as np
from scipy.signal import find_peaks


def estimate_noise(
        data: np.array,
        min_peak_width: float
) -> float:
    """
    Estimates the noise within data by identifying all noise peaks (all peaks with a peak width lower than a given
    cutoff width). Calculates the average noise as the mean of the peak heights.

    Args:
        data: Numpy array of the raw data.
        min_peak_width: Peak width cutoff under which peaks are considered noise.
    """
    all_peaks, _ = find_peaks(data)
    signal_peaks, _ = find_peaks(data, width=min_peak_width)
    noise_peaks: np.array = np.setdiff1d(all_peaks, signal_peaks)

    average_noise: float = np.mean(data[noise_peaks])
    if np.isnan(average_noise):
        return None
    return average_noise
