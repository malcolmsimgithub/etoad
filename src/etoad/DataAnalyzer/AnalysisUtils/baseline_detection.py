import numpy as np
from scipy import sparse
from scipy.spatial import ConvexHull
from scipy.sparse.linalg import spsolve


def als_baseline_detection(
        values: np.ndarray,
        smoothing: float,
        weighting: float,
        iterations=10
) -> np.ndarray:
    """
    Detects the baseline of a given numpy array using the algorithm of asymmetric least squares smoothing.
    (P.H.C. Eilers, Kwantitatieve Methoden 1987, 8, 45-64 // P. H. C Eilers, H. Boelens, 2005).

    Args:
        values: 1D Numpy array of values to determine the baseline in.        smoothing: Smoothing parameter (the larger, the smoother the baseline)
        weighting: Weights of deviations (between 0 and 0.5, the smaller, the stronger peak suppression)
        iterations: Iterations for the solver (default: 10)

    Returns:
        baseline: Fitted baseline
    """
    length: int = len(values)
    d_matrix = sparse.diags([1, -2, 1], [0, -1, -2], shape=(length, length-2))
    d_matrix = smoothing * d_matrix.dot(d_matrix.transpose())
    w_vector = np.ones(length)
    w_matrix = sparse.spdiags(np.ones(length), 0, length, length)
    baseline: np.ndarray = np.zeros(length)

    for _ in range(iterations):
        w_matrix.setdiag(w_vector)
        z_matrix = w_matrix + d_matrix
        baseline: np.ndarray = spsolve(z_matrix, w_vector * values)
        w_vector = weighting * (values > baseline) + (1 - weighting) * (values < baseline)

    return baseline


def als_baseline_removal(
        values: np.ndarray,
        smoothing: float,
        weighting: float,
        iterations=10
) -> np.ndarray:
    """
    Removes the baseline of a given numpy array using the algorithm of asymmetric least squares smoothing.
    (P.H.C. Eilers, Kwantitatieve Methoden 1987, 8, 45-64 // P. H. C Eilers, H. Boelens, 2005).

    Args:
        values: 1D Numpy array of values to determine the baseline in.
        smoothing: Smoothing parameter (the larger, the smoother the baseline)
        weighting: Weights of deviations (between 0 and 0.5, the smaller, the stronger peak suppression)
        iterations: Iterations for the solver (default: 10)

    Returns:
        values_corrected: Array with removed baseline
    """
    baseline = als_baseline_detection(values, smoothing, weighting, iterations)
    return values - baseline


def rubberband_baseline_detection(
        x_values: np.ndarray,
        y_values: np.ndarray,
) -> np.array:
    """
    Performs rubberband fitting of a spectral baseline.

    Since the rubberband fitting itself can only operate on data with positive peaks and ascending x values,
    a series of checks and data transformations is applied initially.

    Identifies a convex hull around the spectrum by identifying the local minima of the data as the hull vertices.
    Rolls the hull vertices to start by the one with the minimum value, then takes them in ascending order.
    Generates the baseline as a linear interpolation of the hull vertices.

    Args:
        x_values: Numpy array of the x values.
        y_values: Numpy array of the y values.

    Returns:
        Numpy ndarray of the baseline.r
    """
    ascending: bool = True
    positive_peaks: bool = True

    # Checks if x values are in ascending order (required for interpolation), converts data otherwise
    if x_values[1] < x_values[0]:
        ascending = False
        x_values = np.flip(x_values)
        y_values = np.flip(y_values)

    # Checks if peaks are in the positive direction (max deviation from median), converts data otherwise
    max_peak_idx = abs(y_values - np.median(y_values)).argmax()
    if y_values[max_peak_idx] < np.median(y_values):
        positive_peaks = False
        y_values = -y_values

    # Performs rubberband baseline fitting
    hull_vertex_indices: np.ndarray = ConvexHull(np.column_stack((x_values, y_values))).vertices
    indices_rolled: np.ndarray = np.roll(hull_vertex_indices, -hull_vertex_indices.argmin())
    indices_final = indices_rolled[:indices_rolled.argmax()]
    baseline: np.array = np.interp(x_values, x_values[indices_final], y_values[indices_final])

    # Performs re-transformation of the data, if applicable.
    if not ascending:
        baseline = np.flip(baseline)
    if not positive_peaks:
        baseline = -baseline

    return baseline


def rubberband_baseline_removal(
        x_values: np.ndarray,
        y_values: np.ndarray,
):
    """
    Performs a rubberband fitting of the spectral baseline. Subtracts the baseline from the y values, and returns
    the corrected y values.

    Args:
        x_values: Numpy array of the x values.
        y_values: Numpy array of the y values.

    Returns:
        Numpy ndarray of the corrected y values.
    """
    baseline: np.ndarray = rubberband_baseline_detection(x_values, y_values)
    return y_values - baseline
