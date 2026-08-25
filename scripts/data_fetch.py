# scripts/data_fetch.py

import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
BASE_URL = 'https://fantasy.premierleague.com/api/'

class FPLClient:
    """
    Resilient HTTP Client for Fantasy Premier League API.
    Handles browser header emulation, connection pooling, and automatic retries.
    """
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://fantasy.premierleague.com/',
        })

        # Retry strategy on rate limits (429) or transient server errors (500, 502, 503, 504)
        retries = Retry(
            total=4,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

        # Optional session cookie authentication if provided in .env
        pl_profile = os.getenv('FPL_COOKIE')
        if pl_profile:
            self.session.cookies.set('pl_profile', pl_profile, domain='fantasy.premierleague.com')

    def get(self, endpoint: str, params: dict = None) -> requests.Response:
        url = f"{BASE_URL}{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=10)
        return response

# Global singleton client instance
_client = FPLClient()

def get_gw_status():
    """
    Fetch the overall game status (e.g., current event, deadlines).
    """
    r = _client.get('bootstrap-static/')
    r.raise_for_status()
    return r.json().get('events', None)

def get_gw_finished_status(gw_no: int) -> bool:
    """
    Fetch game week finished status.
    """
    r = _client.get('bootstrap-static/')
    r.raise_for_status()
    events = r.json().get('events', [])
    if 1 <= gw_no <= len(events):
        return events[gw_no - 1]['finished']
    return False

def get_league_id(league_name: str) -> int:
    """
    Look up the league ID from environment variables.
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
    """
    r = _client.get(f"entry/{manager_id}/")
    r.raise_for_status()
    return r.json()

def get_league_manager_id(league_id: int) -> list:
    """
    Get all manager IDs from a classic league (paged API).
    Supports both active season (standings.results) and preseason (new_entries.results).
    """
    manager_ids = []
    page_no = 1
    has_next = True
    
    # 1. Try active season standings first
    while has_next:
        r = _client.get(f"leagues-classic/{league_id}/standings/", params={'page_standings': page_no})
        r.raise_for_status()
        page = r.json()
        
        standings_results = page.get('standings', {}).get('results', [])
        for entry in standings_results:
            if 'entry' in entry:
                manager_ids.append(entry['entry'])
            
        has_next = page.get('standings', {}).get('has_next', False)
        page_no += 1

    # 2. If standings is empty (preseason before GW1), check new_entries
    if not manager_ids:
        page_no = 1
        has_next = True
        while has_next:
            r = _client.get(f"leagues-classic/{league_id}/standings/", params={'page_new_entries': page_no})
            r.raise_for_status()
            page = r.json()
            
            new_entries = page.get('new_entries', {}).get('results', [])
            for entry in new_entries:
                if 'entry' in entry:
                    manager_ids.append(entry['entry'])
                
            has_next = page.get('new_entries', {}).get('has_next', False)
            page_no += 1

    # Preserve order while ensuring unique manager IDs
    seen = set()
    unique_manager_ids = []
    for mid in manager_ids:
        if mid not in seen:
            seen.add(mid)
            unique_manager_ids.append(mid)

    return unique_manager_ids

def get_dim_managers(league_id: int) -> pd.DataFrame:
    """
    Get detailed info for all managers in a league.
    """
    manager_ids = get_league_manager_id(league_id)
    data = []
    for manager_id in manager_ids:
        manager_info = get_manager_info(manager_id)
        if manager_info:
            keys_to_keep = [
                'id',
                'player_first_name',
                'player_last_name',
                'name',
                'entered_events',
                'last_deadline_bank',
                'last_deadline_value',
                'last_deadline_total_transfers'
            ]
            filtered_manager_info = {k: manager_info.get(k) for k in keys_to_keep}
            data.append(filtered_manager_info)
            
    if not data:
        return pd.DataFrame(columns=['id', 'player_first_name', 'player_last_name', 'name', 'entered_events'])

    return pd.DataFrame(data)

def get_dim_players() -> pd.DataFrame:
    """
    Get metadata for all players (e.g., name, team, position, price).
    """
    r = _client.get('bootstrap-static/')
    r.raise_for_status()
    return pd.DataFrame(r.json()['elements'])

def get_manager_picks(manager_id: int, gw_no: int) -> dict:
    """
    Get a manager's selected squad for a given gameweek.
    Returns None if the manager entry/picks are not found.
    """
    url = f"entry/{manager_id}/event/{gw_no}/picks/"
    try:
        r = _client.get(url)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as err:
        if err.response is not None and err.response.status_code == 404:
            print(f"Skipping: Manager {manager_id} not found for GW {gw_no} (likely joined late).")
            return None
        else:
            raise
    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")
        return None

def get_gw_points(league_id: int, gw_no: int) -> pd.DataFrame:
    """
    Calculate points, rank, and H2H score for all managers in a gameweek.
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
        data['manager_id'].append(manager_id)
        data['gw_no'].append(gw_no)
        
        if picks:
            history = picks.get('entry_history', {})
            data['points'].append(history.get('points', 0))
            data['transfers_cost'].append(history.get('event_transfers_cost', 0))
            data['active_chip'].append(picks.get('active_chip'))
            data['points_on_bench'].append(history.get('points_on_bench', 0))
        else:
            data['points'].append(0)
            data['transfers_cost'].append(0)
            data['active_chip'].append(None)
            data['points_on_bench'].append(0)

    return pd.DataFrame(data)