# scripts/main.py

import argparse
from config import ACTIVE_LEAGUES, SEASON
from data_fetch import get_gw_finished_status, get_league_id, get_gw_points
from data_read_write import write_gw_raw, read_gw_raw, write_gw_analyzed
from data_analyze import calc_weekly_pnl

def run_weekly_fetch_raw(league_name: str, gw_no: int, season: str = None):
    print(f"Fetching raw data for league: {league_name}, GW: {gw_no} ({season or SEASON})")

    # Fetch league ID from environment
    league_id = get_league_id(league_name)

    # Fetch gameweek points
    gw_points = get_gw_points(league_id, gw_no)

    # Write raw data
    write_gw_raw(gw_points, league_name, gw_no, season=season)

    print("Fetch raw data completed successfully.")

def run_weekly_pnl(league_name: str, gw_no: int, season: str = None):
    print(f"Calculating PnL for league: {league_name}, GW: {gw_no} ({season or SEASON})")
    
    # Read gw_points from csv file
    gw_points = read_gw_raw(league_name, gw_no, season=season)

    # Calculate PnL/prizes
    gw_pnl = calc_weekly_pnl(gw_points, league_name)

    # Write analyzed
    write_gw_analyzed(gw_pnl, league_name, gw_no, season=season)

def main():
    parser = argparse.ArgumentParser(description="Run weekly FPL data pipeline.")
    parser.add_argument("--league", type=str, required=True, choices=ACTIVE_LEAGUES, help="League short code")
    parser.add_argument("--gw", type=int, required=True, help="Gameweek number")
    parser.add_argument("--season", type=str, default=SEASON, help="Season string (e.g. 2026-2027)")
    parser.add_argument("--skip-assert", action="store_true", help="Skip gameweek finished assertion check (for testing)")

    args = parser.parse_args()
    league_name = args.league
    gw_no = args.gw
    season = args.season

    if not args.skip_assert:
        assert get_gw_finished_status(gw_no), f"Gameweek {gw_no} not finished yet."

    run_weekly_fetch_raw(league_name, gw_no, season=season)
    run_weekly_pnl(league_name, gw_no, season=season)

if __name__ == "__main__":
    main()