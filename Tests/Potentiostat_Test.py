import threading
from pathlib import Path

from etoad.HardwareController.Potentiostat.EChemController import EChemController
from etoad.Interface import GraphicalInterface
from etoad.Utils import timestamp_datetime, get_dropbox_path


PARENT_DIR = get_dropbox_path() / "PythonScript" / "EChem" / "Settings"

logger = GraphicalInterface(
    logging_config=PARENT_DIR / "logger_settings_v2.json",
    log_file=Path(f"Test_Potentiostat_{timestamp_datetime()}.log")
)


def do_measurement():

    potentiostat = EChemController(
        config_file=PARENT_DIR / "potentiostat_settings.json",
        logger=logger,
        simulation_mode=False
    )

    logger.sample_name = "K4[Fe(CN)6]"

    _ = potentiostat.do_measurement(
        technique="CV",
        set_parameters={
            "IterationSettings": {
                "no_iterations": 3
            },
            "TechniqueParameters": {
                "Voltage Profile": {
                    "value": [0.5, 0.5, 0, 0.5, 0.5]
                },
                "Scan Rate": {
                    "changed_over_iterations": True,
                    "value": [
                        [0.01, 0.01, 0.01, 0.01, 0.01],
                        [0.1, 0.1, 0.1, 0.1, 0.1],
                        [1, 1, 1, 1, 1],
                    ]
                },
                "Number of Cycles": {
                    "value": 5
                }
            }
        }
    )

    potentiostat.disconnect()
    logger.stop_gui()


worker_thread = threading.Thread(target=do_measurement)
worker_thread.start()
logger.start_gui()
worker_thread.join()

"""
# Performs a Cyclic Voltammetry Measurement (5 Cycles between 0.5 and -0.5 V)

potentiostat.load_technique(
    technique="CV",
    set_parameters={
        "Voltage Profile": [0.5, 0.5, -0.5, 0.5, 0.5],
        "Number of Cycles": 5
    }
)

results: np.ndarray = potentiostat.do_measurement()

potentiostat.disconnect()
"""