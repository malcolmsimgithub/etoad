#!/usr/bin/env python

import os, sys
import time

planners = ['RandomSearch', 'Gpyopt', 'Gryffin', 'Botorch']

datasets = ['buchwald_a','buchwald_b','buchwald_c','buchwald_d','buchwald_e']

cwd = os.getcwd()

for planner in planners:
	for dataset in datasets:

		os.chdir(f'{planner}/{dataset}')
		os.system('pwd')
		# submit job
		os.system('sbatch submit.sh')
		time.sleep(5)

		os.chdir(cwd)
