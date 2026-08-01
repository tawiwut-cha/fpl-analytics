# scripts/data_fetch.py

import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
base_url = 'https://fantasy.premierleague.com/api/'

def get_gw_status():
    """
    Fetch the overall game status (e.g., current event, deadlines).
    
    Parameters:
    
    Returns:
        dict: JSON response from the FPL API.
    """
    r = requests.get(base_url + 'bootstrap-static/')
    r.raise_for_status()
    return r.json().get('events', None)

def get_gw_finished_status(gw_no: int):
    """
    Fetch game week status

    Parameters:
        gw_no (int): Gameweek number

    Returns:
        bool: True or False whether gw is finished
    """
    # see gameweek general info
    r = requests.get(base_url + 'bootstrap-static/')
    r.raise_for_status()
    return r.json()['events'][gw_no - 1]['finished']
    


def get_league_id(league_name: str) -> int:
    """
    Look up the league ID from environment variables.
    
    Parameters:
        league_name (str): Short code name for the league (e.g., 'rbsc').
    
    Returns:
        int: League ID corresponding to the league name.
    
    Raises:
        ValueError: If the league name is not found in environment variables.
    """
    env_var = f"LEAGUE_ID_{league_name.upper()}"
    value = os.getenv(env_var)
    if value:
        return int(value)
    else:
        raise ValueError(f"Invalid league name: {league_name}. Did you set {env_var} in .env?")


def get_manager_info(manager_id: int) -> dict:
    """
    Fetch basic information about a manager.
    
    Parameters:
        manager_id (int): FPL manager's entry ID.
    
    Returns:
        dict: Manager metadata (name, team name, region, etc.).
    """
    r = requests.get(f"{base_url}entry/{manager_id}/")
    r.raise_for_status()
    return r.json()


def get_league_manager_id(league_id: int) -> list:
    """
    Get all manager IDs from a classic league (paged API).
    
    Parameters:
        league_id (int): League ID.
    
    Returns:
        list: List of manager IDs.
    """
    manager_ids = []
    page_no = 1
    has_next = True
    while has_next:
        r = requests.get(f"{base_url}leagues-classic/{league_id}/standings/?page_standings={page_no}")
        r.raise_for_status()
        page = r.json()
        has_next = page['standings']['has_next']
        page_no += 1
        for entry in page['standings']['results']:
            manager_ids.append(entry['entry'])
    return manager_ids


def get_dim_managers(league_id: int) -> pd.DataFrame:
    """
    Get detailed info for all managers in a league.
    
    Parameters:
        league_id (int): League ID.
    
    Returns:
        pd.DataFrame: Manager metadata.
    """
    manager_ids = get_league_manager_id(league_id)
    data = []
    for manager_id in manager_ids:
        manager_info = get_manager_info(manager_id)
        keys_to_keep = {
            'id',
            'player_first_name',
            'player_last_name',
            'name',
            'entered_events',
            'last_deadline_bank',
            'last_deadline_value',
            'last_deadline_total_transfers'
        }
        filtered_manager_info = {k: v for k, v in manager_info.items() if k in keys_to_keep}
        data.append(filtered_manager_info)
    return pd.DataFrame(data)

def get_dim_players() -> pd.DataFrame:
    """
    Get metadata for all players (e.g., name, team, position, price).
    
    Returns:
        pd.DataFrame: DataFrame of player information.
    """
    r = requests.get(base_url + 'bootstrap-static/')
    r.raise_for_status()
    return pd.DataFrame(r.json()['elements'])


def get_manager_picks(manager_id: int, gw_no: int) -> dict:
    """
    Get a manager's selected squad for a given gameweek.
    Returns None if the manager entry/picks are not found.
    """
    url = f"{base_url}entry/{manager_id}/event/{gw_no}/picks/"
    
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
        
    except requests.exceptions.HTTPError as err:
        # Check if it's a 404 error (Not Found)
        if err.response.status_code == 404:
            print(f"Skipping: Manager {manager_id} not found for GW {gw_no} (likely joined late).")
            return None
        else:
            # Re-raise if it's a different HTTP error (e.g., 500, 403)
            raise
            
    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")
        return None


# def get_manager_transfers(manager_id: int, gw_no: int) -> dict:
#     """
#     Get a manager's transfer activity for a given gameweek.
    
#     Parameters:
#         manager_id (int): Manager entry ID.
#         gw_no (int): Gameweek number (unused in API but kept for signature consistency).
    
#     Returns:
#         dict: List of transfer activities.
#     """
#     r = requests.get(f"{base_url}entry/{manager_id}/transfers/")
#     r.raise_for_status()
#     return r.json()


# def get_gw_picks(league_id: int, gw_no: int) -> pd.DataFrame:
#     """
#     Aggregate the picks (selected players) for all managers in a league.
    
#     Parameters:
#         league_id (int): League ID.
#         gw_no (int): Gameweek number.
    
#     Returns:
#         pd.DataFrame: Picks data with manager labels.
#     """
#     manager_ids = get_league_manager_id(league_id)
#     gw_picks = []
#     for manager_id in manager_ids:
#         picks = get_manager_picks(manager_id, gw_no)['picks']
#         for pick in picks:
#             pick['manager_id'] = manager_id
#         gw_picks.extend(picks)
#     return pd.DataFrame(gw_picks)


def get_gw_points(league_id: int, gw_no: int) -> pd.DataFrame:
    """
    Calculate points, rank, and H2H score for all managers in a gameweek.
    Handles managers who joined late by assigning None to missing data.
    """
    manager_ids = get_league_manager_id(league_id)
    data = {
        'manager_id': [],
        'gw_no': [],
        'points': [],
        'transfers_cost': [],
        'active_chip': [],
        'points_on_bench': [],
    }

    for manager_id in manager_ids:
        picks = get_manager_picks(manager_id, gw_no)
        
        # Append manager info regardless of whether picks exist
        data['manager_id'].append(manager_id)
        data['gw_no'].append(gw_no)
        
        if picks:
            # Extract data if picks are found
            history = picks.get('entry_history', {})
            data['points'].append(history.get('points', 0))
            data['transfers_cost'].append(history.get('event_transfers_cost', 0))
            data['active_chip'].append(picks.get('active_chip'))
            data['points_on_bench'].append(history.get('points_on_bench', 0))
        else:
                    # Assign 0 instead of None to ensure math operations work later
                    data['points'].append(0)
                    data['transfers_cost'].append(0)
                    data['active_chip'].append(None) # Chips are strings, None is fine here
                    data['points_on_bench'].append(0)

    df = pd.DataFrame(data)
    return df