from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Tuple

import numpy as np

from etoad.Utils import ConfigLoader


class EChemDataAnalyzer(metaclass=ABCMeta):
    """
    Abstract Base Class for an analyzer object for specific electrochemical techniques.

    Instantiation requires the following args:
        analysis_settings: Dictionary of all analysis steps to be performed, and the corresponding specifications.
        raw_data: Numpy.ndarray of the raw experimental data to be analyzed.

    Public Methods:
        run_analysis(): Performs all analysis steps specified in the analysis_settings

    Abstract Methods:
        _set_methods(): Specify the factory pattern for all specific analysis operations (to be implemented for the
                        respective technique).
    """
    analysis_method_name: str = ""

    def __init__(
            self,
            analysis_settings: dict,
            raw_data: np.ndarray
    ):
        """
        Instantiates the EChemDataAnalyzer.

        Args:
            analysis_settings: Dictionary of all possible analysis steps as keys and the respective specifications.
                               Provided settings override the default configs given in $analysis_method_name$.json
            raw_data: Numpy ndarray of the raw experimental data.

        Sets the following attributes:
            self._analysis_steps: Specifications for each analysis step (from default and passed configs)
            self._analysis_methods: Factory pattern for calling the specific analysis techniques.
            self._raw_data: Raw data to be analyzed.
            self._analysis_results: Dictionary of all analysis results per analysis step.
            self._figures: Dictionary of all generated Figure objects.
        """
        self._analysis_steps: dict = self._get_config(analysis_settings)

        self._analysis_methods: dict = {}
        self._set_methods()

        self._raw_data: np.ndarray = raw_data
        self._analysis_results: dict = dict()
        self._figures: dict = dict()



    @abstractmethod
    def _set_methods(
            self
    ):
        """
        Sets the self._methods factory pattern dictionary according to the specific analysis methods
        declared for the analyzer.
        """
        raise NotImplementedError

    def _load_default_config(
            self
    ) -> dict:
        """
        Loads the default analysis settings from the $METHOD_Defaults.json located in the same folder
        and returns the dictionary:

        Returns:
            Dictionary of default settings.
        """
        default_file: Path = Path(__file__).parent / f"{self.analysis_method_name}_Defaults.json"
        return ConfigLoader.load_config(default_file)

    def _get_config(
            self,
            analysis_steps: dict
    ) -> dict:
        """
        Completes the parameter set for each analysis step to be performed by adding default values
        for missing parameters.

        Args:
            analysis_steps: Dictionary of analysis steps and configurations.

        Returns:
            updated_steps: Updated parameter dictionary.
        """
        default_config: dict = self._load_default_config()

        updated_steps: dict = {}

        for step in analysis_steps:
            updated_steps[step] = default_config[step]
            updated_steps[step].update(analysis_steps[step])

        return updated_steps

    def _separate_iterations(
            self
    ) -> None:
        """
        Separates the raw CV data into a dictionary of np.ndarrays. Each key represents the iteration number.
        Each ndarray represents one CV iteration.
        Overrides self._raw_data.
        """

        no_iterations: int = int(np.max(self._raw_data[:, -1]) + 1)
        self._raw_data = [self._raw_data[self._raw_data[:, -1] == iteration] for iteration in range(no_iterations)]
        # TODO: Same discussion as in the CV analyzer. Why is this a dictionary? (FSK, Sep 13)
        for no_iteration in range(no_iterations):
            self._analysis_results[f"iteration_{no_iteration}"] = {}

    def run_analysis(
            self,
    ) -> Tuple[dict, dict]:
        """
        Abstract method.
        Performs all the data analysis steps specified in the analysis_methods dictionary.

        Returns:
            self._analysis results: Dictionary of all analysis results.
            self._figures: Dictionary of all _figure objects created upon analysis.
        """
        for step, step_config in zip(self._analysis_steps, self._analysis_steps.values()):
            self._analysis_methods[step](**step_config)

        return self._analysis_results, self._figures
