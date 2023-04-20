from contextlib import contextmanager
from pathlib import Path
from typing import Union, Any, Optional, List
import numpy as np

from .Interface import GraphicalInterface
from .Utils import ConfigLoader
from .Utils import SkipExecution, StopExecution
from .Utils import ThreadWithReturn
from .HardwareController import EChemController, SamplingSystem
from .DataAnalyzer import DataAnalyzer


class WorkflowManager(object):
    """
    High-level controller to perform complex pre-defined workflows for electrochemical compound characterization.
    Manages the following processes:
        - sample preparation and sample transfer (via the SamplingSystem package)
        - electrochemical measurements (via the EChemController package)
        - data analysis (via the EChemAnalyzer package) and downstream decision-making
        - data storage

    For a detailed description of the workflow settings file (json format), see documentation.

    Public methods:
        measure_sample(sample_name: str, sample_location: int, workflow_path: Path) -> None
    """
    # TODO: include threading

    _required_settings: set = {
        "Protocol Name",
        "Steps",
        "Sample Volume",
        "Total Volume",
        "Discard Sample",
        "Purge",
        "Wash"
    }

    _exception_keywords: dict = {
        "SKIP": SkipExecution,
        "STOP": StopExecution
    }

    def __init__(
            self,
            logger_settings: Path,
            potentiostat_settings: Path,
            sampler_settings: Path,
            data_path: Path,
            logfile: Optional[Path] = None
    ):
        """
        Instantiates the workflow manager object by instantiating the individual modules:
            - self.logger
            - self.potentiostat (EChemController object)
            - self.sampling_system (SamplingSystem object)
            - self.analyzer (DataAnalyzer object)

        Args:
            logger_settings: Path to the json file containing the logger settings
            potentiostat_settings: Path to the json file containing the potentiostat settings
            sampler_settings: Path to the json file containing the sampler settings
            data_path: Path to the folder where data should be stored.
            logfile: Optional - name of the logfile used.
        """
        # TODO: Refactor to hide private attributes
        self.logger: GraphicalInterface = GraphicalInterface(logger_settings, log_file=logfile)
        self.potentiostat_settings = potentiostat_settings
        self.sampler_settings = sampler_settings
        self.data_path = data_path

        self.potentiostat: Optional[EChemController] = None
        self.sampling_system: Optional[SamplingSystem] = None
        self.analyzer: Optional[DataAnalyzer] = None

        self.samples: list = list()

    def submit_samples(self, samples: List[dict]) -> None:
        """
        Public method to submit all samples to measure to the WorkflowManager.
        Each sample should be given as a dictionary with the keys "sample_name", "sample_location" and "workflow_path".
        Must be called before the system is started.

        Args:
            samples: List of samples (each one given as a dictionary)

        Raises:
            KeyError if any of the samples does not contain all required keys.
        """
        for sample in samples:
            if {"sample_name", "sample_location", "workflow_path"}.issubset(sample.keys()):
                self.samples.append(sample)
            else:
                raise KeyError(f"The settings for sample {sample} are inclomplete.")

    def start_system(self) -> dict:
        """
        Public method to start all measurements previously loaded to the WorkflowManager.
        Starts the multithreaded operation:
            - main thread: GUI
            - side thread: Measurement

        Returns:
            dict: Dictionary of all results.

        Raises:
            ValueError if no samples have been loaded.
        """
        if not self.samples:
            raise ValueError("No samples have been submitted – system initialization will be skipped.")

        measurements = ThreadWithReturn(target=self._run_system)
        measurements.start()
        self.logger.start_gui()
        results: dict = measurements.join()
        return results

    def _run_system(self):
        """
        Method to run the entire WorkflowManager – needs to be started on a separate thread with the GUI active.
        Initializes the potentiostat, sampling system and analyzer.
        Runs the measurement for each sample in the samples attribute.
        Closes the system after all measurements are completed, and sends the "close" command to the GUI
        (will eventually liberate the main thread).
        """
        self.initialize_system()

        results: dict = dict()
        for sample in self.samples:
            results[sample["sample_name"]] = self._measure_sample(**sample)

        self.shutdown_system()
        return results

    def initialize_system(self, initial_wash: int = 1, sample_in_cell: bool = True) -> None:
        """
        Initializes the system by initializing the potentiostat, the sampling system and the data analyzer.

        Args:
            initial_wash: Number of initial syringe washes.
            sample_in_cell: If the cell needs to be emptied before starting the workflow.
        """
        self.logger.info("SYSTEM INITIALIZATION")
        self.potentiostat: EChemController = EChemController(self.potentiostat_settings, logger=self.logger)
        self.sampling_system: SamplingSystem = SamplingSystem(self.sampler_settings, logger=self.logger, initial_wash=initial_wash, cell_filled=sample_in_cell)
        self.analyzer: DataAnalyzer = DataAnalyzer(self.data_path, logger=self.logger)

    def _measure_sample(
            self,
            sample_name: str,
            sample_location: int,
            workflow_path: Path
    ) -> dict:
        """
        Executes a specified measurement workflow for a given sample.

        Args:
            sample_name: Name of the sample to be measured
            sample_location: Position of the sample on the autosampler.
            workflow_path: Path to the json file that specifies the workflow to be executed.

        Returns:
            result: Dictionary of all steps executed and their respective results.
        """
        # TODO: rename the sample by including a timestamp?
        workflow: dict = ConfigLoader.load_config(workflow_path, self._required_settings)
        self.logger.info(f"Starting Protocol {workflow['Protocol Name']} for sample {sample_name}.")
        self.logger.sample_name = sample_name

        result: dict = {"Sample Name": sample_name, "Workflow": workflow["Protocol Name"]}

        with self._sample_in_cell(
            autosampler_position=sample_location,
            sample_volume=workflow["Sample Volume"],
            total_volume=workflow["Total Volume"],
            purge_time=workflow["Purge"],
            discard_sample=workflow["Discard Sample"],
            **workflow["Wash"]
        ):
            for step, step_details in zip(workflow["Steps"], workflow["Steps"].values()):
                try:
                    result: dict = self._execute_step(sample_name, step, result, **step_details)
                except SkipExecution:
                    self.logger.info(f"Execution of {step} will be skipped.")
                    continue
                except StopExecution:
                    break

        return result

    def _execute_step(
            self,
            sample_name: str,
            step_name: str,
            previous_results: dict,
            **kwargs
    ) -> Any:
        """
        Factory pattern for executing a specific operation, as specified in the workflow.

        Args:
            sample_name: Name of the sample to be run.
            step_name: Name of the step to be executed (key in the settings file).
            previous_results: Dictionary of all results from previous steps.
            kwargs: Keyword arguments for the specific step to be executed.
        """
        executable_steps: dict = {
            "measure": self.run_measurement,
            "dilute": self._dilute_cell,
        }
        self.logger.info(f"Now executing {step_name}.")

        return executable_steps[kwargs["task"]](sample_name, step_name, previous_results, **kwargs)

    @contextmanager
    def _sample_in_cell(
            self,
            autosampler_position: int,
            sample_volume: float,
            total_volume: float,
            purge_time: float,
            discard_sample: bool,
            wash_volume: float = 5,
            washing_cycles: int = 3
    ) -> None:
        """
        Context manager for transferring a sample to the measurement cell (before the first measurement),
        and emptying and washing the cell (after the final measurement).

        Args:
             autosampler_position: Vial number on the autosampler.
             sample_volume: Volume to be transferred to the cell.
             total_volume: Total volume of the sample in the cell (after dilution).
             purge_time: Time for purging with nitrogen gas.
             wash_volume: Volume to wash the cell.
             washing_cycles: Iterations for washing the cell
        """
        self.logger.experiment_name = "Filling Cell"
        self.sampling_system.transfer_to_cell(autosampler_position, sample_volume)
        self.sampling_system.dilute_cell(volume=total_volume-sample_volume)
        self.logger.info(f"Sample was successfully transferred to the measurement cell ({sample_volume} + {total_volume-sample_volume} mL).")
        self.sampling_system.purge_cell(purge_time)
        self.logger.experiment_name = "Purging Cell"
        try:
            yield

        # TODO: Put an exception handling here to log possible exception tracebacks before the finally block is reached
        #       Requires knowing the types of exception, or catching the parent class of exception, which might be
        #       dangerous
        #       Alternative: Catch Exception as sth, log the traceback, and then raise sth again
        #                    That definitely requires some trying before...I have never done that before

        finally:
            self.logger.info(f"Measurements for sample completed.")
            self.logger.experiment_name = "Emptying Cell"
            if discard_sample:
                self.sampling_system.wash_autosampler_position(autosampler_position)
            self.sampling_system.wash_cell(wash_volume, washing_cycles)

    def run_measurement(
            self,
            sample_name: str,
            step_name: str,
            results: dict,
            technique: str,
            parameters: dict,
            update_parameters: list,
            analysis_settings: dict,
            channel: Union[int, None] = None,
            **kwargs
    ) -> dict:
        """
        Runs a specified measurement on the instrument by loading the technique, running the measurement and evaluating
        the data.

        Args:
            sample_name: Name of the measurement.
            step_name: Name of the step to be executed.
            results: Dictionary for storing all previous results.
            technique: Name of the measurement technique
            parameters: Dictionary of measurement parameters deviating from the default values.
            update_parameters: List of dictionaries of parameters that need to be inferred from previous measurements.
            analysis_settings: Dictionary of keywords and specifications for data analysis.
            channel: Measurement channel (if None, the default channel is selected).
        """
        if update_parameters:
            parameters = self._update_parameters(
                update_settings=update_parameters,
                parameters=parameters,
                previous_results=results)

        raw_data: np.ndarray = self.potentiostat.do_measurement(
            technique=technique,
            set_parameters=parameters,
            channel=channel
        )

        analysis_results: dict = self.analyzer.analyze_data(
            sample_name=sample_name,
            experiment_name=step_name,
            technique=technique,
            analysis_settings=analysis_settings,
            raw_data=raw_data
        )

        results[step_name] = analysis_results
        return results

    def _dilute_cell(
            self,
            sample_name: str,
            step_name: str,
            results: dict,
            **kwargs
    ):
        """
        Executes the dilution of the sample in the measurement cell by calling the method from the
        sampling system object.

        Args:
            sample_name: Name of the sample                   ATTN: Only required for uniform code structure.
            step_name: Name of the step                       ATTN: Only required for uniform code structure.
            results: Dictionary of previous results
            kwargs: Keyword arguments for the dilute_cell method (either "volume" or "factor")
        """
        self.sampling_system.dilute_cell(**kwargs)
        results["dilution"] = True

        return results

    def _update_parameters(
            self,
            update_settings: list,
            parameters: dict,
            previous_results: dict
    ) -> dict:
        """
        Updates the parameter dictionary from the results of previous measurements.

        Structure of the update_settings list:
        [
            {
                "parameter": Name of the parameter to be updated
                "from measurement": Name of the measurement performed
                "key": Key in the results dictionary for this measurement.
            },
            ...
        ]

        Args:
            update_settings: List of parameters to be updated (structure see above).
            parameters: Dictionary of measurement parameters to be passed to the potentiostat.
            previous_results: Dictionary of all previous results.

        Raises:
            WorkflowException (according to keywords in self._exception_keywords) if skipping / cancelling is triggered.
        """
        # TODO: Dobule-check how that method works with the new iterative measurement technique
        for param_to_update in update_settings:
            new_value: Any = previous_results[param_to_update["from measurement"]][param_to_update["key"]]

            if isinstance(new_value, str):
                if new_value in self._exception_keywords:
                    raise self._exception_keywords[new_value]

            parameters[param_to_update["parameter"]] = new_value

        return parameters

    def shutdown_system(
            self,
            fill_cell: bool = True
    ) -> None:
        """
        Transfers 5 mL solvent to the sample cell for keeping the electrode surfaces wet.
        Shuts the system down by disconnecting from the potentiostat and the sampling system.
        Sends the stop command to the GUI and liberates the main thread.
        """
        if fill_cell:
            self._dilute_cell("shutdown", "shutdown", volume=5.0, results={})
        self.potentiostat.disconnect()
        self.sampling_system.disconnect()
        self.logger.stop_gui()

