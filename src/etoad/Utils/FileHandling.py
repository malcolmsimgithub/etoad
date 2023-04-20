import json
import pickle

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any


def save_as_pkl(
        object_to_save: Any,
        file_name: Path
) -> None:
    """
    Saves the passed Python object into a pickle file.

    Args:
        object_to_save: Object to be saved (any type).
        file_name: Path to the file where the pkl file should be stored.
    """
    with open(file_name, "wb") as pklfile:
        pickle.dump(object_to_save, pklfile)


def save_as_csv(
        data: np.ndarray,
        file_name: Path
) -> None:
    """
    Saves a 1D or 2D Numpy array into a csv file using pandas.

    Args:
        data: 1D or 2D Numpy array.
        file_name: Path to the file where the csv should be stored.
    """
    data_df: pd.DataFrame = pd.DataFrame(data)
    data_df.to_csv(file_name, index=False, header=False)


def save_as_json(
        data: dict,
        file_name: Path
) -> None:
    """
    Saves a dictionary or list (or any other json-serializable object) into a json file.

    Args:
        data: Dictionary to save.
        file_name: Path to the file where the json file should be stored.
    """
    with open(file_name, "w") as json_file:
        json.dump(data, json_file, indent=2, separators=(",", ": "))
