import numpy as np
import pandas as pd
import os
from stochastic_generation import Generate_stochastic_data
import warnings
warnings.filterwarnings('ignore')
def Read_data(file_dir, filenames):
    graph_file = os.path.join(file_dir, filenames[0])
    pre_prod_file = os.path.join(file_dir, filenames[1])
    infec_file = os.path.join(file_dir, filenames[2])
    relaxpara_file = os.path.join(file_dir, filenames[3])
    data_dict = {}
    # graph = pd.read_csv("data_graph.csv") #read csv with data related to regions, their businesses and possible trade 
    print(graph_file)
    graph = pd.read_csv(graph_file) #read csv with data related to regions, their businesses and possible trade 
    # prod = pd.read_csv(prod_file) #read csv with data related to regions and their businesses information
    infec = pd.read_csv(infec_file) #read csv with data related to region information 
    relaxpara = pd.read_csv(relaxpara_file) # read cvs with parameter used in relaxed soft constraints model
    prod = Generate_stochastic_data(pre_prod_file)
    data_dict['graph'] = graph
    data_dict['prod'] = prod
    data_dict['infec'] = infec
    data_dict['relaxpara'] = relaxpara

    I = graph.region.unique().size #Compute number of regions
    J = graph.business.unique().size #Compute number of businesses
    data_dict['I'] = I
    data_dict['J'] = J

    trade = [] 
    trade_orig_dest = np.zeros((I,I,J))
    trade_orig = []
    #Loop to determine businesses that trade
    for r in range(graph.business.size):
        if graph['region'][r] != graph['trade_region'][r]:
            trade.append(graph['business'][r])
            trade_orig.append(graph['region'][r])
            trade_orig_dest[graph['region'][r],graph['trade_region'][r],graph['business'][r]] = 1
    trade_orig_ar = list( dict.fromkeys(trade_orig) ) 
    trade_orig_ar.sort()
    trade_ar = list( dict.fromkeys(trade) ) 
    trade_ar.sort()
    data_dict['trade_ar'] = trade_ar
    J1 = len(trade_ar) #Number of businesses that involve trade
    J2 = J-J1
    T = 6 #Inserted by hand, but could then be automated...
    num_scenario = 5 
    data_dict['T'] = T
    data_dict['num_scenario'] = num_scenario

    #Set supply and demand graph
    #Here define all the edges between state for each business
    #Loop to determine all the possible edges that involve trade
    Edge = [None]*J #I use J and not J1 since the order of the businesses matter 
    for e in trade_ar:
        Edge[e] = []
        for r in range(graph.business.size):
            if graph['business'][r] == e:
                if graph['region'][r] != graph['trade_region'][r]:
                    Edge[e].append((graph['region'][r],graph['trade_region'][r]))
    data_dict['Edge'] = Edge

    #Loop to determine the profit of the above registered Edges 
    Profit = [None]*J
    for j in range(J):
        Profit[j] = {}
    prof_lab = []
    for i in range(T):
        prof_lab.append(f'Profit{i+1}')
    for x in trade_ar:
        for z in range(len(Edge[x])):
            Profit[x][Edge[x][z]] = graph[(graph['region']==Edge[x][z][0]) & (graph['business']==x) & (graph['trade_region']==Edge[x][z][1])][prof_lab].values
            Profit[x][Edge[x][z]] = Profit[x][Edge[x][z]][0].tolist()
    data_dict['Profit'] = Profit

    #Loop to extract profit of local business
    Q = np.zeros((I,J,T))
    for x in range(I):
        for y in range(J):
            Q[x,y,:] = graph[(graph['region']==x) & (graph['business']==y) & (graph['trade_region']==x)][prof_lab].values
    data_dict['Q'] = Q

    prod_lab = []
    for i in range(T):
        prod_lab.append(f'prod_cap{i+1}')
    #Loop to extract production capacity (uncertain)
    R = np.zeros((num_scenario,I,J,T))
    for xi in range(num_scenario):
        for x in range(I):
            for y in range(J):
                R[xi,x,y,:] = prod[(prod['scenario']==xi) & (prod['region']==x) & (prod['business']==y)][prod_lab].values
    data_dict['R'] = R
    
    dem_lab = []
    for i in range(T):
        dem_lab.append(f'demand{i+1}')
    #Loop to extract demand
    D = np.zeros((num_scenario,I,J,T))
    for xi in range(num_scenario):
        for x in range(I):
            for y in range(J):
                D[xi,x,y,:] = prod[(prod['scenario']==xi) & (prod['region']==x) & (prod['business']==y)][dem_lab].values     
    data_dict['D'] = D

    unemp_lab = []
    for i in range(T):
        unemp_lab.append(f'unemp{i+1}')
    #Loop to extract Unemployed people
    S = np.zeros((I,J,T))
    for x in range(I):
        for y in range(J):
            S[x,y,:] = prod[(prod['scenario']==0) & (prod['region']==x) & (prod['business']==y)][unemp_lab].values     
    data_dict['S'] = S

    imp_lab = []
    for i in range(T):
        imp_lab.append(f'importance{i+1}')
    # importance of opening business
    delta = np.zeros((I,J,T))
    for x in range(I):
        for y in range(J):
            delta[x,y,:] = prod[(prod['scenario']==0) & (prod['region']==x) & (prod['business']==y)][imp_lab].values     
    data_dict['delta'] = delta

    acc_lab = []
    for i in range(T):
        acc_lab.append(f'acc_unemp{i+1}')
    #Loop to extract accepted unemployed people
    v = np.zeros((I,T))
    for x in range(I):
            v[x,:] = infec[(infec['region']==x)][acc_lab].values     
    data_dict['v'] = v

    weight_lab = []
    for i in range(T):
        weight_lab.append(f'weight_inf{i+1}')
    #Loop to extract weight of infected people
    W = np.zeros((I,T))
    for x in range(I):
            W[x,:] = infec[(infec['region']==x)][weight_lab].values     
    data_dict['W'] = W

    infr_lab = []
    for i in range(T):
        infr_lab.append(f'inf_rate{i+1}')
    #Loop to extract infection rate
    alpha = np.zeros((I,T))
    for x in range(I):
            alpha[x,:] = infec[(infec['region']==x)][infr_lab].values     
    data_dict['alpha'] = alpha

    rec_lab = []
    for i in range(T):
        rec_lab.append(f'rec_rate{i+1}')
    #Loop to extract recovery rate
    beta = np.zeros((I,T))
    for x in range(I):
            beta[x,:] = infec[(infec['region']==x)][rec_lab].values     
    data_dict['beta'] = beta

    #Recovery period 
    T0 = 3 #For now entered by hand
    data_dict['T0'] = T0

    infb_lab = []
    for i in range(T):
        infb_lab.append(f'inf_bus{i+1}')
    #Loop to extract infected people for each business
    B = np.zeros((num_scenario,I,J,T))
    for xi in range(num_scenario):
        for x in range(I):
            for y in range(J):
                B[xi,x,y,:] = prod[(prod['scenario']==xi) & (prod['region']==x) & (prod['business']==y)][infb_lab].values     
    data_dict['B'] = B

    #Loop to extract initial infected people
    a0 = np.zeros(I)
    for x in range(I):
        a0[x] = infec[(infec['region']==x)][['initial_inf']].values 
    data_dict['a0'] = a0    

    acci_lab = []
    for i in range(T):
        acci_lab.append(f'acc_inf{i+1}')
    #Loop to extract acceptable infected people
    c = np.zeros((I,T))
    for x in range(I):
        c[x,:] = infec[(infec['region']==x)][acci_lab].values     
    data_dict['c'] = c

    #Loop to extract intensive rate
    int_lab = []
    for i in range(T):
        int_lab.append(f'int_rate{i+1}')
    h = np.zeros((I,T))
    for x in range(I):
            h[x,:] = infec[(infec['region']==x)][int_lab].values    
    data_dict['h'] = h 

    #Loop to extract ICU capacity
    icu_lab = []
    for i in range(T):
        icu_lab.append(f'icu_cap{i+1}')
    k = np.zeros((I,T))
    for x in range(I):
            k[x,:] = infec[(infec['region']==x)][icu_lab].values 
    data_dict['k'] = k    

    # medical equipment parameters

    #Loop for testing kits if no business opened
    tkno_lab = []
    for i in range(T):
        tkno_lab.append(f'tk_nobus{i+1}')
    f = np.zeros((I,T))
    for x in range(I):
            f[x,:] = infec[(infec['region']==x)][tkno_lab].values   
    data_dict['f'] = f  

    #Loop for PPE if no business opened
    ppeno_lab = []
    for i in range(T):
        ppeno_lab.append(f'ppe_nobus{i+1}')
    m = np.zeros((I,T))
    for x in range(I):
            m[x,:] = infec[(infec['region']==x)][ppeno_lab].values    
    data_dict['m'] = m 

    #Loop for tk requiered of business j opens
    tkbus_lab = []
    for i in range(T):
        tkbus_lab.append(f'tk_bus{i+1}')
    g = np.zeros((I,J,T))
    for x in range(I):
        for y in range(J):
            g[x,y,:] = prod[(prod['scenario']==0) & (prod['region']==x) & (prod['business']==y)][tkbus_lab].values
    data_dict['g'] = g

    #Loop for ppe requiered of business j opens
    ppebus_lab = []
    for i in range(T):
        ppebus_lab.append(f'ppe_bus{i+1}')
    n = np.zeros((I,J,T))
    for x in range(I):
        for y in range(J):
            n[x,y,:] = prod[(prod['scenario']==0) & (prod['region']==x) & (prod['business']==y)][ppebus_lab].values
    data_dict['n'] = n

    #Loop for maximum tk available in region i 
    tkmax_lab = []
    for i in range(T):
        tkmax_lab.append(f'tk_max{i+1}')
    l = np.zeros((I,T))
    for x in range(I):
            l[x,:] = infec[(infec['region']==x)][tkmax_lab].values 
    data_dict['l'] = l    

    #Loop for maximum ppe available in region i 
    ppemax_lab = []
    for i in range(T):
        ppemax_lab.append(f'ppe_max{i+1}')
    u = np.zeros((I,T))
    for x in range(I):
            u[x,:] = infec[(infec['region']==x)][ppemax_lab].values     
    data_dict['u'] = u

    #Loop for initial state
    x0 = np.zeros((I,J))
    for x in range(I):
        for y in range(J):
            x0[x,y] = prod[(prod['scenario']==0) & (prod['region']==x) & (prod['business']==y)][['init_state']].values
    data_dict['x0'] = x0
    
    #Loop for parameters used in relaxed soft constraints model
    time_lab = []
    for i in range(1,T):
        time_lab.append(f'time{i+1}')
    num_cons = 5 # number of soft constraints
    gamma = np.zeros((num_cons,I,T-1))
    for cons in range(num_cons):
        for x in range(I):
            gamma[cons,x,:] = relaxpara[(relaxpara['constraint']==cons) & (relaxpara['region']==x)][time_lab].values
    data_dict['gamma'] = gamma
    return data_dict
