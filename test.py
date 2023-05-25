import pickle
import etoad

from etoad.DataAnalyzer import DataAnalyzer




with open("Tests/Test_Cyclic_SWV.pkl", "rb") as f:
    data = pickle.load(f)

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


print(type(data))



analyzer = DataAnalyzer("analysisresults")