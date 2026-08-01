# scripts/maintenance.py

import argparse
from config import ACTIVE_LEAGUES, SEASON
from data_fetch import get_league_id, get_dim_managers
from data_read_write import write_dim_managers

def update_dim_managers(league_name: str, season: str = None):
    """
    Refreshes the manager metadata (dim_managers.csv) for a given league.
    """
    print(f"Refreshing manager metadata for league: {league_name} ({season or SEASON})...")
    league_id = get_league_id(league_name)
    dim_managers = get_dim_managers(league_id)
    write_dim_managers(dim_managers, league_name, season=season)

def main():
    parser = argparse.ArgumentParser(description="Refresh manager metadata for active leagues.")
    parser.add_argument("--league", type=str, choices=ACTIVE_LEAGUES, help="Optional specific league short code")
    parser.add_argument("--season", type=str, default=SEASON, help="Season string (e.g. 2026-2027)")
    args = parser.parse_args()

    leagues_to_run = [args.league] if args.league else ACTIVE_LEAGUES
    for league_name in leagues_to_run:
        update_dim_managers(league_name, season=args.season)

if __name__ == "__main__":
    main()