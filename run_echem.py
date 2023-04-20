import pickle
import numpy as np
import pandas as pd

# import matplotlib.pyplot as plt
from matplotlib import pyplot as plt
import seaborn as sns

from olympus.objects import (
        ParameterContinuous,
        ParameterDiscrete,
        ParameterCategorical,
)
from olympus.planners import Planner
from olympus.campaigns import Campaign, ParameterSpace
from olympus.surfaces import Surface

from olympus.utils.misc import get_hypervolume

from atlas.optimizers.gp.planner import BoTorchPlanner

from etoad import WorkflowManager

from pathlib import Path


#################################
# make parameter space          #
#################################

#TODO make param space

param_space = ParameterSpace()

# add ligand --> general parameter
param_space.add(
    ParameterCategorical(
        name='diquots',
        options=[str(i) for i in range(3)],
        descriptors=[None for i in range(3)],        # add descriptors later
    )
)
# add temperature
param_space.add(
    ParameterContinuous(
        name='rest time ti',
        low=1,
        high=60.
    )
)
# add residence time
param_space.add(
    ParameterContinuous(
        name='Pulse height (mV)',
        low=1,
        high=1000.
    )
)
# add catalyst loading
# summit expects this to be in nM
param_space.add(
    ParameterContinuous(
        name='Step Height (mV)',
        low=1,
        high=100,
    )
)

param_space.add(
    ParameterContinuous(
        name='percent of end of pulse to measure',
        low=1,
        high=100,
    )
)

param_space.add(
    ParameterCategorical(
        name='electrolyte',
        options=["NaCl","KCl","LiCl"],
        descriptors=[None for i in range(3)],        # add descriptors later
    )
)


param_space.add(
    ParameterContinuous(
        name='temperature',
        low=25,
        high=50,
    )
)

param_space.add(
    ParameterContinuous(
        name='electrolyte concentration(M)',
        low=0.1,
        high=2,
    )
)

param_space.add(
    ParameterContinuous(
        name='degassing time (s)',
        low=1,
        high=60,
    )
)

param_space.add(
    ParameterCategorical(
        name='electrode',
        options=["glassy carbon", "pt disk"],
        descriptors=[None for i in range(2)],        # add descriptors later
    )
)

param_space.add(
    ParameterContinuous(
        name='pulse width (ms)',
        low=2,
        high=100,
    )
)


#################################
# make value space              #
#################################

value_space = ParameterSpace()
value_space.add(ParameterContinuous(name='FWHM'))
value_space.add(ParameterContinuous(name='SN ratio'))

#######################################
# make etoad WorkflowManager          #
#######################################

tests = Path("./Tests/test_settings/")

echem = WorkflowManager(
        logger_settings=tests/"logger_settings.json",
        potentiostat_settings=tests/"potentiostat_settings.json",
        sampler_settings=tests/"sampler_settings.json",
        data_path="etoad_data",
        logfile="etoad_log.log",
        )

all_campaigns = []
all_true_measurements = []
all_hvols = []


#################################
# Bayesian Optimization         #
#################################

BUDGET = 25
NUM_RUNS = 15


for run in range(NUM_RUNS):
    
    campaign = Campaign()
    campaign.set_param_space(param_space)

    planner = BoTorchPlanner(
        ############ TODO DESIGN STRATEGY
        goal='minimize',
        init_design_strategy='random',
        num_init_design=5,
        batch_size=1,
        acquisition_optimizer_kind='gradient',
        ########### TODO GENERAL PARAMETERS
        general_parmeters=[0],
        is_moo=True,
        scalarizer_kind='Hypervolume', 
        ###### TODO VALUE SPACE
        value_space=value_space,
        goals=['min', 'max'],   
    )
    planner.set_param_space(param_space)

    true_measurements = []
    hvols = []

    for iter_ in range(BUDGET):

        return_params = planner.recommend(campaign.observations)

        samplelist = [] 


        for sample in return_params:

                # TODO: format params into a dicts for sample list


                samplelist.append(sample)

        
        echem.submit_samples(samplelist)

        results = echem.start_system()

        #TODO: analyze results and add to campaign
        results_formatted = results

        print(f'ITER : {iter_}\tSAMPLES : {return_params}\t MEASUREMENT : {results_formatted}')
        campaign.add_observation(return_params, results)

    all_true_measurements.append(true_measurements)
    all_hvols.append(hvols)
    all_campaigns.append(campaign)