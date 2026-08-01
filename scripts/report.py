# scripts/report.py

import argparse
from config import ACTIVE_LEAGUES, SEASON
from data_read_write import read_gw_analyzed, read_dim_managers, write_report

def generate_weekly_pnl_report(league_name: str, gw_no: int, season: str = None):
    # Load data
    analyzed_df = read_gw_analyzed(league_name, gw_no, season=season)      
    managers_df = read_dim_managers(league_name, season=season)

    # Merge to get manager names
    df = analyzed_df.merge(managers_df, left_on="manager_id", right_on="id", how="left")

    # Filter out rows with PnL == 0
    df = df[df["pnl"] != 0]

    # Add full name column for display
    df["full_name"] = df["player_first_name"].fillna('') + " " + df["player_last_name"].fillna('')

    # Separate winners and losers
    winners = df[df["pnl"] > 0].sort_values("pnl", ascending=False)
    losers = df[df["pnl"] < 0].sort_values("pnl")

    # Format each line
    format_line = lambda row: f"{row['pnl']:+.0f}: {row['name']} ({row['full_name']}) {row['points']} - {row['transfers_cost']} = {row['h2h_points']} pts"

    # Build message lines
    lines = []
    lines.append(f"📊 GW{gw_no:02d} {league_name.upper()} H2H Results\n")

    if not winners.empty:
        lines.append("💰 Winners:")
        lines.extend([format_line(row) for _, row in winners.iterrows()])
        lines.append("")  # empty line

    if not losers.empty:
        lines.append("💸 Losers:")
        lines.extend([format_line(row) for _, row in losers.iterrows()])

    # Final report string
    report = "\n".join(lines)

    # Output to file
    write_report(report, league_name, gw_no, season=season)
    print(f"\nReport preview for {league_name.upper()} GW{gw_no:02d}:\n")
    print(report)

def main():
    parser = argparse.ArgumentParser(description="Generate text report from analyzed scores.")
    parser.add_argument("--league", type=str, required=True, choices=ACTIVE_LEAGUES, help="League short code")
    parser.add_argument("--gw", type=int, required=True, help="Gameweek number")
    parser.add_argument("--season", type=str, default=SEASON, help="Season string (e.g. 2026-2027)")

    args = parser.parse_args()
    generate_weekly_pnl_report(args.league, args.gw, season=args.season)

if __name__ == "__main__":
    main()
