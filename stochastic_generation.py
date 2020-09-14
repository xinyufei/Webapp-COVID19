import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore') 
from scipy.stats import uniform
from scipy.stats import norm
from scipy.stats import gamma
from scipy.stats import expon
import os
def Generate_stochastic_data(pre_prod_file):
    # THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    # pre_prod_file = os.path.join(THIS_FOLDER, 'data_prod_clnw_test.csv')
    print(pre_prod_file)
    pre_prod = pd.read_csv(pre_prod_file) #read csv with data related to regions and their businesses
    pre_prod.insert(0,'scenario',0)
    num_scenario = 5
    T = 6
    scenario_lab = []
    scenario_lab.append('state')
    scenario_lab.append('region')
    scenario_lab.append('industry')
    scenario_lab.append('business')
    for i in range(T):
        scenario_lab.append(f'prod_cap{i+1}')
        scenario_lab.append(f'demand{i+1}')
        scenario_lab.append(f'inf_bus{i+1}')
    uni = pre_prod
    for j in range(len(uni['scenario'])):
        for k in range(T):
            uni[f'prod_cap{k+1}'][j] = norm.rvs(pre_prod[f'prod_cap{k+1}'][j],pre_prod[f'prod_cap{k+1}'][j]/10)
            uni[f'demand{k+1}'][j] = norm.rvs(pre_prod[f'demand{k+1}'][j],pre_prod[f'demand{k+1}'][j]/10)
            uni[f'inf_bus{k+1}'][j] = norm.rvs(pre_prod[f'demand{k+1}'][j],pre_prod[f'demand{k+1}'][j]/10)
    for i in range(1,num_scenario):
        sce = pre_prod[scenario_lab]
        sce.insert(0,'scenario',i)
        for j in range(len(sce['scenario'])):
            for k in range(T):
                sce[f'prod_cap{k+1}'][j] = norm.rvs(pre_prod[f'prod_cap{k+1}'][j],pre_prod[f'prod_cap{k+1}'][j]/10)
                sce[f'demand{k+1}'][j] = norm.rvs(pre_prod[f'demand{k+1}'][j],5*pre_prod[f'demand{k+1}'][j]/10)
                sce[f'inf_bus{k+1}'][j] = norm.rvs(pre_prod[f'inf_bus{k+1}'][j],5*pre_prod[f'inf_bus{k+1}'][j]/10)
        uni = pd.concat([uni,sce],ignore_index=True)
    # uni.to_csv("data_prod_stochastic.csv",index=False)
    return uni
