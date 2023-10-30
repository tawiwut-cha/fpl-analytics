### Do fun stuff with FPL data !
import requests
import pandas as pd

base_url = 'https://fantasy.premierleague.com/api/'

# League id 

def get_league_id(league_name):
    league_ids = {
        'rbsc': 532134,
        'rpk': 766550,
        'ifc': 805760,
    }
    try:
        return league_ids[league_name]
    except KeyError:
        print('Please enter a valid league name', league_ids.keys)

# Manager data

def get_league_manager_id(league_id:int):
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

def get_manager_info(manager_id:int) -> dict:
    '''Basic info on FPL Manager'''
    r = requests.get(base_url+'entry/'+str(manager_id))
    assert r.status_code == 200, r.status_code
    return r.json() 

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

# Player data

def get_players():
    return pd.read_csv('data/player_idlist.csv')

# GW Points data

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

# GW Picks data

def get_gw_picks(league_id, gw_no):
    '''Returns a dataframe of selected players.'''
    manager_ids = get_league_manager_id(league_id)
    data = pd.DataFrame()
    for manager_id in manager_ids:
        manager_data = pd.DataFrame(get_manager_picks(manager_id, gw_no)['picks'])
        manager_data['manager_id'] = manager_id
        data = pd.concat([data, manager_data], ignore_index=True)
    return data


def get_gw_captains(league_id, gw_no):
    '''Returns a dataframe of captains and number of managers captaining each.'''
    pass


def get_gw_transfers(league_id, gw_no):
    '''Returns a dataframe of transfers and the count of how many.'''
    pass

# GW Ranking calculations for weekly local leagues

def get_gw_weekly_pnl(gw, league_name:str):
    if league_name == 'rbsc':
        return pnl_rbsc(gw)
    elif league_name == 'ifc':
        return pnl_ifc(gw)
    
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
    return gw[gw.pnl != 0]

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
    return gw[gw.pnl != 0]

## Respect Kruwai
# TODO



# Create dataframe for EDA on season long rankings -> เพราะเราใช้ sql น่าจะง่ายกว่า ใช้ api เพื่อดึงข้อมูลมาทำเป็นตารางให้ได้พอ

if __name__ == '__main__':
    # ไป eda ต่อเล่น ใน jupyter แล้ว ถ้าชอบอะไรค่อยมาสร้างเป็น function visualizations.py แยกอีกทีได้
    # args
    gw_no = 10
    league_name = 'rbsc'
    # main
    league_id = get_league_id(league_name)
    gw = get_gw_points(league_id, gw_no)
    pnl = get_gw_weekly_pnl(gw, league_name)
    # picks = get_gw_picks(gw_no)
    print('yo')