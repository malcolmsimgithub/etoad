# Electrochemical Technique Operation for Autonomous Discovery: E-Toad

E-Toad is a modular Python package for automating the workflows around electroanalytical characterization of functional materials. 
- Electroanalytical Measurements in Solution using the BioLogic Potentiostat family
- Data Processing, Analysis and Visualization 
- Liquid Sample Transfer using a Tecan Syringe Pump (Hardware Setup Instructions see below)
- Control of Higher-Level Workflows using a Fully Integrated System 


### Installation
```
git clone https://github.com/aspuru-guzik-group/python_echem

cd python-echem

pip install .
```

### Usage (Potentiostat Only)
```
from etoad import EChemController, GraphicalInterface

gui = GraphicalInterface(
    logging_config=test_dir / "logger_settings.json",
    logfile=Path.cwd() / "Test.log"
)

potentiostat = EChemController(
    config_file=test_dir / "potentiostat_settings.json",
    logger=gui
)
```