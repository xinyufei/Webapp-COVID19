import pandas as pd
import gurobipy as gb
import math
import numpy as np
from data_extraction_stochastic import Read_data
from reopen_relax_stochastic import Reopen_relax_stochastic
from reopen_stochastic import Reopen_stochastic
import warnings
warnings.filterwarnings('ignore')
# build model with basic constraints, no soft constraints
#Loop to split\ the information by state, in order to make forecasts by state, this could be lead further for every county in the dataset. 

def print_result(file_dir, filenames):
    # Read data from input file
    data_dict = Read_data(file_dir, filenames)
    I = data_dict['I']
    J = data_dict['J']
    T = data_dict['T']
    num_scenario = data_dict['num_scenario']
    trade_ar = data_dict['trade_ar']
    Profit = data_dict['Profit']
    Edge = data_dict['Edge']
    Q = data_dict['Q']
    prod = data_dict['prod']

    m_reopen, y, z, a, x, t_init, t_fin = Reopen_stochastic(data_dict)
    #Profit obtained from trade activities
    y_value = [None]*J
    for j in trade_ar:
        y_value[j] = m_reopen.getAttr('x', y[j])
    y_val = np.zeros((num_scenario,J,I,I,T))
    for j in trade_ar:
        for (i1,i2) in Edge[j]:        
            for t in range(T):
                for xi in range(num_scenario):
                    y_val[xi,j,i1,i2,t] = Profit[j][i1,i2][t]*y_value[j][(i1,i2,t,xi)]
    trade_profit = [None]*num_scenario
    for i in range(num_scenario):
        trade_profit[i] = sum(Profit[j][i1,i2][t]*y_value[j][(i1,i2,t,i)] for j in trade_ar for (i1,i2) in Edge[j] for t in range(T))

    #Profit obtained from internal activities
    z_value = m_reopen.getAttr('x', z)
    z_res = np.zeros((num_scenario,I,J,T))
    for xi in range(num_scenario):
        for i in range(I):
            for j in range(J):
                for t in range(T):
                    z_res[xi,i,j,t] = Q[i,j,t]*z_value[i,j,t,xi]
    internal_profit = [None]*num_scenario
    for xi in range(num_scenario):
        internal_profit[xi] = sum(z_res[xi,i,j,t] for i in range(I) for j in range(J) for t in range(T))

    z_reg=np.zeros((num_scenario,I,J))
    for xi in range(num_scenario):    
        for i in range(I):
            for j in range(J):
                z_reg[xi,i,j] = sum(z_res[xi,i,j,t] for t in range(T))
            
    profit_orig_dest = np.zeros((num_scenario,I,J,I))
    for xi in range(num_scenario):
        for j in trade_ar:
            for (i1,i2) in Edge[j]:
                profit_orig_dest[xi][i1][j][i2] = sum(Profit[j][i1,i2][t]*y_value[j][(i1,i2,t,xi)] for t in range(T)) 

    profit_orig_bus = np.zeros((num_scenario,I,J))
    for xi in range(num_scenario):
        for i in range(I):
            for j in range(J):
                profit_orig_bus[xi][i][j] = sum(profit_orig_dest[xi][i][j][k] for k in range(I))

    state_total = np.zeros((num_scenario,I,J))
    for xi in range(num_scenario):
        for i in range(I):
            for j in range(J):
                state_total[xi][i][j] = z_reg[xi,i,j]+profit_orig_bus[xi,i,j]
                
    #Infected people by region by time (a)
    a_value = m_reopen.getAttr('x',a)
    a_res = np.zeros((num_scenario,I,T))
    for xi in range(num_scenario):
        for i in range(I):
            for t in range(T):
                a_res[xi,i,t] = a_value[i,t,xi]
    a_sum =[None]*num_scenario
    for xi in range(num_scenario):
        a_sum[xi] = math.ceil(sum(a_res[xi,i,T-1] for i in range(I)))
    #obtaining region names and business names 
    region = prod.state.unique()
    industry = prod.industry.unique()

    x_value = m_reopen.getAttr('x',x)
    x_result = np.zeros((I,J,T))
    import os
    # THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    # writer_file = os.path.join(THIS_FOLDER, 'model_reopen_solution.xlsx')
    writer_file = file_dir + '\model-reopen-solution.xlsx'
    writer = pd.ExcelWriter(writer_file,engine='xlsxwriter')   # Creating Excel Writer Object from Pandas  
    workbook=writer.book
    for xi in range(num_scenario):
        rcount = 0
        rcount = rcount+7 
        for i in range(I):
            for j in range(J):
                for t in range(T):
                    x_result[i,j,t] = x_value[i,j,t]

            df = pd.DataFrame(data=x_result[i])
            df['Decision'] = 0
            df['Economic benefit'] = 0
            df['Internal benefit'] = 0
            df['Trade benefit'] = 0
            for l in range(J):
                for k in range(T-1):
                    if df[k][l] != df[k+1][l]:
                        p = df[k][l]
                        o = df[k+1][l]
                        if o - p == 1:
                            df['Decision'][l] = f'Reopen in time {k+1}'
                        if o - p == -1:
                            df['Decision'][l] = f'Close in time {k+1}'
                        break
                    if df[k][l] == 1:
                        df['Decision'][l] = 'Industry needs to remain open'
                    elif df[k][l] == 0:
                        df['Decision'][l] = 'Industry needs to remain closed'
                df['Economic benefit'][l] = state_total[xi][i][l]
                df['Trade benefit'][l] = profit_orig_bus[xi][i][l]
                df['Internal benefit'][l] = z_reg[xi][i][l]
                    
                    
            df = df.add_prefix('Time ')
            df = df.rename(index=lambda s: f'{industry[s]}')
            df = df.rename(columns={'Time Decision':'Decision',
                                    'Time Economic benefit':'Economic Benefit $M',
                                    'Time Internal benefit':'Internal Benefit $M',
                                    'Time Trade benefit':'Trade Benefit $M'})
            #df.index = [1, 2, 3]
            df.to_excel(writer,sheet_name=f'Scenario_{xi}',startrow=rcount , startcol=0)
            worksheet = writer.sheets[f'Scenario_{xi}']
            worksheet.write(rcount-1,0, f'{region[i]}')
            worksheet.write(rcount-1,1, f'Active cases on last time step = {math.ceil(a_res[xi,i,T-1])}' )
        
            rcount = rcount+len(df.index)+3
        title = 'Solution for the basic model'

        worksheet.write(0,0,title)  
        worksheet.write(1,0,f'Runtime: {t_fin-t_init} sec')
        worksheet.write(2,0,f'{a_sum[xi]} active cases on last time step for the regions')
        worksheet.write(3,0,f'${trade_profit[xi]+internal_profit[xi]} M dlls of economic benefit for the reopening phases')
        worksheet.write(4,0,f'Objective value: ${m_reopen.objVal}')

    writer.save()