import pickle
from pathlib import Path
import json
from typing import Any, Union


class ConfigLoader(object):

    @classmethod
    def load_config(cls, config_file: Path, required_keys: Union[set, None] = None) -> dict:
        """
        Loads a configuration from a defined file type and returns the corresponding dictionary.

        Args:
            config_file: Path to the config file.
            required_keys: List of keys that the dictionary needs to contain.

        Returns:
            config: Dictionary of configurations.

        Raises:
            TypeError: Loaded object is not a valid configuration (i.e. no dictionary).
        """
        config: Any = cls.load_file(config_file)

        if not isinstance(config, dict):
            raise TypeError("A Configuration must be a dictionary object.")

        if required_keys:
            if not required_keys.issubset(config):
                raise ValueError("The settings do not contain all required keys.")

        return config

    @classmethod
    def load_file(cls, file_name: Path) -> Any:
        """
        Loads a file depending on its file type and returns its content as a Python object.

        Args:
            file_name: Path to the source file.

        Returns:
            loaded_object: Loaded file content as a Python file.

        Raises:
            NotImplemented Error: If file loading for an unknown file type is requested.
        """
        loaders: dict = {
            ".json": cls._load_json,
            ".pkl": cls._load_pkl,
        }

        try:
            loaded_object: Any = loaders[file_name.suffix](file_name)
            return loaded_object
        except KeyError:
            raise NotImplementedError(f"The file type {file_name.suffix} is currently not supported.")

    @staticmethod
    def _load_json(file_name: Path) -> Any:
        """
        Loads a json file and returns the content as a Python object.

        Args:
            file_name: Path to the json file.

        Returns:
            loaded_object: Content of the json file as a Python object.
        """
        with open(file_name, 'r') as jsonfile:
            loaded_object: Any = json.load(jsonfile)

        return loaded_object

    @staticmethod
    def _load_pkl(file_name: Path) -> Any:
        """
        Loads a pkl file and returns the content as a Python object.

        Args:
            file_name: Path to the pkl file.

        Returns:
            loaded_object: Content of the pkl file as a Python object.
        """
        with open(file_name, 'rb') as pklfile:
            loaded_object: Any = pickle.load(pklfile)

        return loaded_object
