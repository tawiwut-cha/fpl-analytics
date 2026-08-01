# read from raw data folder
# apply pnl logic
# write ranked file
import pandas as pd
import numpy as np


def calc_weekly_pnl(gw_points: pd.DataFrame, league_name: str):
    gw = gw_points.copy()
    
    # 1. Separate Active vs Inactive
    # Assuming 'points' is 0 for those who haven't joined
    active_mask = gw['points'] > 0
    active_managers = gw[active_mask].copy()
    inactive_managers = gw[~active_mask].copy()
    
    # 2. Process Ranking only for Active managers
    active_managers['h2h_points'] = active_managers['points'] - active_managers['transfers_cost']
    active_managers['rank'] = active_managers['h2h_points'].rank(method='dense', ascending=False).astype(int)
    
    # 3. Apply PnL logic only to the active subset
    if league_name in {'rbsc', 'bpat', 'balo', 'ytce', 'jmkb'}:
        processed_active = pnl_rbsc(active_managers)
    # ... other leagues ...
    elif league_name == 'ifc':
        processed_active = pnl_ifc(gw)
    elif league_name == 'rpk':
        processed_active = pnl_rpk(gw)
    
    # 4. Set PnL to 0 for inactive managers and clear their rank
    inactive_managers['pnl'] = 0
    inactive_managers['rank'] = 9999  # Assign a high number to push to bottom
    
    # 5. Combine back together
    result = pd.concat([processed_active, inactive_managers])
    
    # 6. Sort by rank so the active ones are on top, inactive on bottom
    result = result.sort_values(by='rank', ascending=True)

    return result
    
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