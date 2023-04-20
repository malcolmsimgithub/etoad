import numpy as np
from DataAnalyzer import DataAnalyzer
import pickle
from pathlib import Path

data_analyzer: DataAnalyzer = DataAnalyzer(Path(r"C:\Users\Lenovo\Desktop\The Matter Lab\Test_Data"))

data_analyzer.analyze_data(
    sample_name="test1",
    experiment_name="test",
    technique="CV",
    analysis_settings={
        "Plot": {"title": "Test CV Measurement", "plot": True},  # TODO: The "Plot" method doesn't have any kwarg named "plot"...
        "Peak Picking": {},
        "Integration": {},
        "Peaks Scanrate": {}

    },
    raw_data=np.load(r"C:\Users\Lenovo\Desktop\The Matter Lab\python_echem\Test_Multi_CV.pkl", allow_pickle=True)
)

# data_analyzer.analyze_data(
#     sample_name="test2",
#     experiment_name="test",
#     technique="SWV",
#     analysis_settings={
#         "Plot": {"title": "Test Multi-SWV Measurement"},
#         "Peak Picking": {},
#         "CV Parameters":{},
#         "Integration": {}
#     },
#     raw_data=np.load(r"C:\Users\Lenovo\Desktop\The Matter Lab\python_echem\Test_Cyclic_SWV.pkl", allow_pickle=True)
# )