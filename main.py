### Do fun stuff with FPL data !
import requests
import pandas as pd
import numpy as np
import os

base_url = 'https://fantasy.premierleague.com/api/'


# 1. Get data

## Get gameweek status
def get_gw_status(gw_no:int):
    r = requests.get(base_url+'bootstrap-static/')
    assert r.status_code == 200, r.status_code
    return None

## League id
def get_league_id(league_name):
    league_ids = {
        'rbsc': 584167,
        'rpk': 748775,
        'ifc': 898742,
    }
    try:
        return league_ids[league_name]
    except KeyError:
        print('Please enter a valid league name', league_ids.keys)

## Player data
def get_dim_players():
    # get latest player info
    r = requests.get(base_url+'bootstrap-static/')
    assert r.status_code == 200, r.status_code
    return pd.DataFrame(r.json()['elements'])

## Manager data

def get_league_manager_id(league_id:int) -> list:
    '''get manager ids from a classic league'''
    manager_id = []
    page_no = 1
    has_next = True
    while has_next:
        r = requests.get(base_url+'leagues-classic/'+str(league_id)+'/standings/'+'?page_standings='+str(page_no))
        assert r.status_code == 200, r.status_code
        this_page = r.json()
        page_no += 1
        has_next = r.json()['standings']['has_next']
        for entry in this_page['standings']['results']:
            manager_id.append(entry['entry'])
    return manager_id

def get_dim_managers(league_id:int):
    '''get manager info from that classic league'''
    manager_ids = get_league_manager_id(league_id)
    data = []
    for manager_id in manager_ids:
        manager_info = get_manager_info(manager_id)
        # delete unwanted info
        del(manager_info['leagues'])
        del(manager_info['kit'])
        data.append(manager_info)
    return pd.DataFrame(data)

def get_manager_info(manager_id:int) -> dict:
    '''Basic info on FPL Manager'''
    r = requests.get(base_url+'entry/'+str(manager_id))
    assert r.status_code == 200, r.status_code
    return r.json() 

## Manager Picks

def get_manager_picks(manager_id:int, gw_no:int) -> dict:
    '''Squad picks of manager for a GW.'''
    r = requests.get(base_url+'entry/'+str(manager_id)+'/event/'+str(gw_no)+'/picks/')
    assert r.status_code == 200, r.status_code
    return r.json() 

def get_manager_transfers(manager_id:int, gw_no:int) -> dict:
    '''Transfers of manager for a GW.'''
    r = requests.get(base_url+'entry/'+str(manager_id)+'/transfers/')
    assert r.status_code == 200, r.status_code
    return r.json() 

## GW Picks data

def get_gw_picks(league_id, gw_no):
    '''Returns a dataframe of selected players.'''
    # manager_ids = get_league_manager_id(league_id)
    # gw_picks = pd.DataFrame()
    # for manager_id in manager_ids:
    #     gw_pick = pd.DataFrame(get_manager_picks(manager_id, gw_no)['picks'])
    #     gw_pick['manager_id'] = manager_id # add manager_id column as label
    #     gw_picks = pd.concat([gw_picks, gw_pick], ignore_index=True)
    # return gw_picks
    manager_ids = get_league_manager_id(league_id)
    gw_picks = []
    for manager_id in manager_ids:
        gw_pick = get_manager_picks(manager_id, gw_no)['picks']
        for pick in gw_pick:
            pick['manager_id'] = manager_id
        gw_picks += gw_pick
    return pd.DataFrame(gw_picks)

## GW Points data

def get_gw_points(league_id, gw_no):
    manager_ids = get_league_manager_id(league_id)
    data = {
        'manager_id': manager_ids,
        'team_name': [],
        'name': [],
        'gw_no': [gw_no]*len(manager_ids),
        'points': [],
        'transfers_cost': [],
        'h2h_points': []
    }
    for manager_id in manager_ids:
        manager = get_manager_info(manager_id)
        data['team_name'].append(manager['name'])
        data['name'].append(manager['player_first_name'] + ' ' + manager['player_last_name'])
        picks = get_manager_picks(manager_id, gw_no)
        data['points'].append(picks['entry_history']['points'])
        data['transfers_cost'].append(picks['entry_history']['event_transfers_cost'])
        data['h2h_points'].append(picks['entry_history']['points'] - picks['entry_history']['event_transfers_cost'])
    df = pd.DataFrame(data)
    df['rank'] = df['h2h_points'].rank(method='dense', ascending=False).astype(int)
    return df.sort_values(by='rank', ascending=True)

# 2. PNL calc

def get_gw_weekly_pnl(gw, league_name:str):
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
    if max(gw['rank']) == len(gw):
        gw['pnl'] = [300,200,100,0,0,-100,-200,-300] # hardcode
        gw['is_unique_rank'] = True
    else:
        gw['pnl'] = np.nan
        gw['is_unique_rank'] = False
    return gw

# 3. Data writing
def write_gw(gw:pd.DataFrame, league_name:str):
    '''write gw data to csv file'''
    location = "data"+"/"+league_name+"/"
    filename = "fact_gw_"+league_name+".csv"
    filepath = location+filename
    gw.to_csv(filepath, index=False)
    print(f"DataFrame successfully saved to {filepath}")


if __name__ == '__main__':
    pass