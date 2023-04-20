from pathlib import Path
from typing import Tuple, Dict
from logging import Logger
import matplotlib.figure
import numpy as np

from ..Utils import timestamp_datetime
from ..Utils import save_as_csv, save_as_json
from .Methods import CVAnalyzer, PulseTechniqueAnalyzer, EChemDataAnalyzer


class DataAnalyzer:
    """
    Minimum viable version of a DataAnalyzer for Electrochemical Data
    """

    _technique_analyzers: dict = {
        "CV": CVAnalyzer,
        "SWV": PulseTechniqueAnalyzer,
        "DPV": PulseTechniqueAnalyzer
    }

    def __init__(
            self,
            data_path: Path,
            logger: Logger
    ):
        """
        Instantiates the general data analyzer.

        Args:
            data_path: Path to the folder where experimental data is stored.
            logger: Logger object
        """
        self._data_path: Path = data_path
        self._logger: Logger = logger

    def analyze_data(
            self,
            sample_name: str,
            experiment_name: str,
            technique: str,
            analysis_settings: dict,
            raw_data: np.ndarray,
    ) -> dict:
        """
        Public method to run the data for a specific electrochemical measurement technique.
        Instantiates the analyzer object for the specific technique and runs the data analysis.

        Args:
            sample_name: Name of the sample to be measured.
            experiment_name: Name of the specific experiment performed.
            technique: Name of the experimental technique.
            analysis_settings: Dictionary of keywords and specifications for data analysis for the specific technique.
            raw_data: Numpy ndarray of the obtained raw data.

        Returns:
            analysis_results: Dictionary of all analysis results returned by the EChemAnalyzer
        """
        sample_dir, basename = self._get_target_folder(sample_name, experiment_name)

        analyzer: EChemDataAnalyzer = self._technique_analyzers[technique](analysis_settings, raw_data)
        analysis_results, figures = analyzer.run_analysis()
        self._logger.info(f"Data Analysis Completed: {analysis_results}")

        self._save_data(raw_data, analysis_results, figures, sample_dir, basename)

        return analysis_results

    def _get_target_folder(
            self,
            sample_name: str,
            experiment_name: str
    ) -> Tuple[Path, str]:
        """
        Sets up the target folder for saving experimental results.

        Args:
            sample_name: Name of the sample to be measured.
            experiment_name: Name of the specific experiment performed.

        Returns:
            sample_dir: Path to the sample-specific data directory.
            file_basename: Basename of the specific experiment ($NAME_$EXP_$TIME)
        """
        sample_dir = self._data_path / sample_name
        sample_dir.mkdir(parents=True, exist_ok=True)

        file_basename = f"{sample_name}_{experiment_name}_{timestamp_datetime()}"

        return sample_dir, file_basename

    def _save_data(
            self,
            raw_data: np.ndarray,
            analysis_results: dict,
            figures: Dict[str, matplotlib.figure.Figure],
            sample_dir: Path,
            file_basename: str
    ) -> None:
        """
        Saves the experimental results (raw data as .pkl and analysis results as .csv) into the target folder.

        Args:
            raw_data: Numpy ndarray of the obtained raw data.
            analysis_results: Dictionary of all analysis results returned by the EChemAnalyzer
        """
        # save_as_pkl(raw_data, sample_dir / f"{file_basename}.pkl")
        save_as_csv(raw_data, sample_dir / f"{file_basename}.csv")
        self._logger.info(f"Raw data was saved to {sample_dir / f'{file_basename}.csv'}")

        # save_as_pkl(analysis_results, sample_dir / f"{file_basename}_analysis.pkl")
        save_as_json(analysis_results, sample_dir / f"{file_basename}_analysis.json")
        self._logger.info(f"Analysis results were saved to {sample_dir / f'{file_basename}_analysis.json'}")

        for fig_name, figure in zip(figures, figures.values()):
            figure.savefig(sample_dir / f"{file_basename}_{fig_name}.png", transparent=True, dpi=600)
