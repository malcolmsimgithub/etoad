from pathlib import Path

from src.etoad.HardwareController import SamplingSystem
from src.etoad.Interface import GraphicalInterface
from src.etoad.Utils.DropboxPath import get_dropbox_path

echem_path: Path = get_dropbox_path() / "PythonScript" / "EChem"

logger = GraphicalInterface(
    logging_config=echem_path / "Settings" / "logger_settings_v2.json"
)

sampler = SamplingSystem(
    config_file=echem_path / "Settings" / "sampler_settings.json",
    logger=logger,
    initial_wash=0,
    cell_filled=True
)

sampler.wash_cell(2)
