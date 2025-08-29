# read from raw data folder
# apply pnl logic
# write ranked file
import pandas as pd
import numpy as np

def calc_weekly_pnl(gw_points: pd.DataFrame, league_name: str):
    gw = gw_points.copy()
    # calc h2h points
    gw['h2h_points'] = gw['points'] - gw['transfers_cost']
    # rank
    gw['rank'] = gw['h2h_points'].rank(method='dense', ascending=False).astype(int)
    gw = gw.sort_values(by='rank', ascending=True)
    # apply pnl logic based on rank
    if league_name == 'rbsc':
        return pnl_rbsc(gw)
    elif league_name == 'ifc':
        return pnl_ifc(gw)
    elif league_name == 'rpk':
        return pnl_rpk(gw)
    
## RBSC
def pnl_rbsc(gw:pd.DataFrame):
    gw = gw.copy()
    # find manager_id rank of winners and losers
    rank = list(gw['rank'])
    max_rank = max(rank)
    min_rank = min(rank)
    max_indices = []
    min_indices = []
    for i in range(len(rank)):
        if rank[i] == max_rank:
            max_indices.append(i)
        elif rank[i] == min_rank:
            min_indices.append(i)
    # assign pnl
    pnl = [0] * len(rank)
    prize = len(max_indices) * 500
    for min_index in min_indices:
        # winner(s)
        pnl[min_index] = round(prize / len(min_indices))
    for max_index in max_indices:
        # loser(s)
        pnl[max_index] = -500
    # assemble resulting dataframe and return
    gw['pnl'] = pnl
    return gw

## IFC
def pnl_ifc(gw:pd.DataFrame):
    gw = gw.copy()
    # find manager_id rank of winners and losers
    rank = list(gw['rank'])
    max_rank = max(rank)
    min_rank = min(rank)
    max_indices = []
    min_indices = []
    for i in range(len(rank)):
        if rank[i] >= max_rank - 2:
            max_indices.append(i)
        elif rank[i] == min_rank:
            min_indices.append(i)
    # assign pnl
    pnl = [0] * len(rank)
    prize = len(max_indices) * 100
    for min_index in min_indices:
        # winner(s)
        pnl[min_index] = round(prize / len(min_indices))
    for max_index in max_indices:
        # loser(s)
        pnl[max_index] = -100
    # assemble resulting dataframe and return
    gw['pnl'] = pnl
    return gw

## Respect Kruwai

def pnl_rpk(gw):
    gw = gw.copy()
    # find manager_id rank of winners and losers
    rank = list(gw['rank'])
    max_rank = max(rank)
    min_rank = min(rank)
    max_indices = []
    min_indices = []
    for i in range(len(rank)):
        if rank[i] >= max_rank - 2:
            max_indices.append(i)
        elif rank[i] == min_rank:
            min_indices.append(i)
    # assign pnl
    pnl = [0] * len(rank)
    prize = len(max_indices) * 100
    for min_index in min_indices:
        # winner(s)
        pnl[min_index] = round(prize / len(min_indices))
    for max_index in max_indices:
        # loser(s)
        pnl[max_index] = -100
    # assemble resulting dataframe and return
    gw['pnl'] = pnl
    return gw