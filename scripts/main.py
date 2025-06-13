import argparse
import sys
import pandas as pd
from data_fetch import get_gw_finished_status, get_league_id, get_gw_points
from data_write import write_gw_raw, read_gw_raw, write_gw_analyzed
from data_analyze import calc_weekly_pnl

def run_weekly_fetch_raw(league_name: str, gw_no: int):
    print(f"Fetching raw data for league: {league_name}, GW: {gw_no}")

    # Fetch league ID from environment
    league_id = get_league_id(league_name)

    # Fetch gameweek points
    gw_points = get_gw_points(league_id, gw_no)

    # Write raw data
    write_gw_raw(gw_points, league_name, gw_no)

    print("Fetch raw data completed successfully.")

def run_weekly_pnl(league_name: str, gw_no: int):
    print(f"Calculating pnl for league: {league_name}, GW: {gw_no}")
    
    # Read gw_points from csv file (single source of truth for now, maybe sql later)
    gw_points = read_gw_raw(league_name, gw_no)

    # Calculate PnL/prizes
    gw_pnl = calc_weekly_pnl(gw_points, league_name)

    # Write analyzed
    write_gw_analyzed(gw_pnl, league_name, gw_no)

def main():
    parser = argparse.ArgumentParser(description="Run weekly FPL data pipeline.")
    parser.add_argument("--league", type=str, required=True, help="League name (e.g., rpk, rbsc, ifc)")
    parser.add_argument("--gw", type=int, required=True, help="Gameweek number")

    args = parser.parse_args()
    league_name = args.league
    gw_no = args.gw

    assert get_gw_finished_status(gw_no), f"Gameweek {gw_no} not finished yet."

    run_weekly_fetch_raw(league_name, gw_no)
    run_weekly_pnl(league_name, gw_no)

if __name__ == "__main__":
    main()