import numpy as np
import gurobipy as gb
from data_extraction_stochastic import *
import time
# penalty parameter
# gamma can be also defined for different regions and time periods 
# gamma = np.ones(5, I, T)*5
# build model with released soft constraints
def Reopen_relax_stochastic(data_dict):
    I = data_dict['I']
    J = data_dict['J']
    T = data_dict['T']
    num_scenario = data_dict['num_scenario']
    T0 = data_dict['T0']
    trade_ar = data_dict['trade_ar']
    Edge = data_dict['Edge']
    Profit = data_dict['Profit']
    Q = data_dict['Q']
    R = data_dict['R']
    D = data_dict['D']
    S = data_dict['S']
    delta = data_dict['delta']
    v = data_dict['v']
    W = data_dict['W']
    alpha = data_dict['alpha']
    beta = data_dict['beta']
    B = data_dict['B']
    c = data_dict['c']
    h = data_dict['h']
    k = data_dict['k']
    f = data_dict['f']
    m = data_dict['m']
    g = data_dict['g']
    n = data_dict['n']
    l = data_dict['l']
    u = data_dict['u']
    x0 = data_dict['x0']
    a0 = data_dict['a0']
    gamma = data_dict['gamma']

    m_reopen = gb.Model()
    y = [None]*J
    for j in trade_ar:
        y[j] = m_reopen.addVars(Edge[j], T, num_scenario, lb=0) # index of variable: (i1,i2,t)
    z = m_reopen.addVars(I, J, T, num_scenario, lb=0)
    x = m_reopen.addVars(I, J, T, vtype = gb.GRB.BINARY)
    a = m_reopen.addVars(I, T, num_scenario, lb=0) # infected people
    r = m_reopen.addVars(5, I, T, num_scenario, lb=0) # auxiliary variable
    m_reopen.update()
    m_reopen.setObjective(gb.quicksum(delta[i,j,t]*x[i,j,t] for i in range(I) for j in range(J) for t in range(1,T)) + 1/num_scenario*(gb.quicksum(Profit[j][i1,i2][t]*y[j][i1,i2,t,xi] for j in trade_ar for (i1,i2) in Edge[j] for t in range(T) for xi in range(num_scenario)) 
        + gb.quicksum(Q[i,j,t]*z[i,j,t,xi] for i in range(I) for j in range(J) for t in range(T) for xi in range(num_scenario))
        - gb.quicksum(W[i,t]*a[i,t,xi] for i in range(I) for t in range(T) for xi in range(num_scenario))
        - gb.quicksum(gamma[cons,i,t-1]*r[cons,i,t-1,xi] for cons in range(5) for i in range(I) for t in range(1,T) for xi in range(num_scenario))), gb.GRB.MAXIMIZE) # objective function
    # economical constraints
    m_reopen.addConstrs(y[j].sum(i,'*',t,xi) + z[i,j,t,xi] <= R[xi][i,j,t]*x[i,j,t] for i in range(I) for j in trade_ar for t in range(T) for xi in range(num_scenario))
    m_reopen.addConstrs(z[i,j,t,xi] <= R[xi][i,j,t]*x[i,j,t] for i in range(I) for j in list(set(range(J))-set(trade_ar)) for t in range(T) for xi in range(num_scenario))
    m_reopen.addConstrs(y[j].sum('*',i,t,xi) + z[i,j,t,xi] <= D[xi][i,j,t]*x[i,j,t] for i in range(I) for j in trade_ar for t in range(T) for xi in range(num_scenario))
    m_reopen.addConstrs(z[i,j,t,xi] <= D[xi][i,j,t]*x[i,j,t] for i in range(I) for j in list(set(range(J))-set(trade_ar)) for t in range(T) for xi in range(num_scenario))
    m_reopen.addConstrs(r[0,i,t-1,xi] - gb.quicksum(S[i,j,t]*x[i,j,t] for j in range(J)) + v[i,t] >= 0 for i in range(I) for t in range(1,T) for xi in range(num_scenario))
    # infected people
    m_reopen.addConstrs(a[i,t+1,xi] >= a[i,t,xi] + alpha[i,t]*a[i,t,xi] + gb.quicksum(B[xi][i,j,t+1]*x[i,j,t+1] for j in range(J)) for i in range(I) for t in range(T0) for xi in range(num_scenario))
    m_reopen.addConstrs(a[i,t+1,xi] >= a[i,t,xi] + alpha[i,t]*a[i,t,xi] + gb.quicksum(B[xi][i,j,t+1]*x[i,j,t+1] for j in range(J)) - beta[i,t-T0]*a[i,t-T0,xi] for i in range(I) for t in range(T0,T-1) for xi in range(num_scenario))
    m_reopen.addConstrs(a[i,0,xi] == a0[i] for i in range(I) for xi in range(num_scenario))
    m_reopen.addConstrs(r[1,i,t-1,xi] - a[i,t,xi] + c[i,t] >= 0 for i in range(I) for t in range(1,T) for xi in range(num_scenario))
    m_reopen.addConstrs(r[2,i,t-1,xi] - h[i,t]*a[i,t,xi] + k[i,t] >= 0 for i in range(I) for t in range(1,T) for xi in range(num_scenario))
    # PPE and testing kits
    m_reopen.addConstrs(r[3,i,t-1,xi] - f[i,t] - gb.quicksum(g[i,j,t]*x[i,j,t] for j in range(J)) + l[i,t] >= 0 for i in range(I) for t in range(1,T) for xi in range(num_scenario))
    m_reopen.addConstrs(r[4,i,t-1,xi] - m[i,t] - gb.quicksum(n[i,j,t]*x[i,j,t] for j in range(J)) + u[i,t] >= 0 for i in range(I) for t in range(1,T) for xi in range(num_scenario))
    # state constraints
    m_reopen.addConstrs(x[i,j,t+1] <= x[i,j,t] + 1 - x0[i,j] for i in range(I) for j in range(J) for t in range(T-1))
    m_reopen.addConstrs(x[i,j,t+1] >= x[i,j,t] - x0[i,j] for i in range(I) for j in range(J) for t in range(T-1))
    m_reopen.addConstrs(x[i,j,0] == x0[i,j] for i in range(I) for j in range(J))
    t_init = time.time()
    m_reopen.optimize()
    t_fin = time.time()
    return m_reopen, y, z, a, x, t_init, t_fin
    # print results of state
    x_value = m_reopen.getAttr('x',x)
    x_result = np.zeros((I,J,T))
    for i in range(I):
        for j in range(J):
            for t in range(T):
                x_result[i,j,t] = x_value[i,j,t]
            print(x_result[i,j,:])
        print("=====================")
    print("objective value: ", m_reopen.objVal)

