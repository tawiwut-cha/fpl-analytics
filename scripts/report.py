# generate text output in the desired format
# send message (how? brainstorm)
import argparse
from data_read_write import read_gw_analyzed, read_dim_managers, write_report

def generate_weekly_pnl_report(league_name, gw_no):
    # Load data
    analyzed_df = read_gw_analyzed(league_name, gw_no)      
    managers_df = read_dim_managers(league_name)

    # Merge to get names
    df = analyzed_df.merge(managers_df, left_on="manager_id", right_on="id")

    # Filter out rows with PnL == 0
    df = df[df["pnl"] != 0]

    # Add full name column for easy display
    df["full_name"] = df["player_first_name"] + " " + df["player_last_name"]

    # Separate winners and losers
    winners = df[df["pnl"] > 0].sort_values("pnl", ascending=False)
    losers = df[df["pnl"] < 0].sort_values("pnl")

    # Format each line
    format_line = lambda row: f"{row['pnl']:+.0f}: {row['name']} ({row['full_name']}) {row['points']} - {row['transfers_cost']} = {row['h2h_points']} pts"

    # Build message lines
    lines = []
    lines.append(f"📊 GW{gw_no:02d} H2H results\n")

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
    write_report(report, league_name, gw_no)


def generate_weekly_fun_fact_report():
    pass

def main():
    parser = argparse.ArgumentParser(description="Generate text report from analyed score.")
    parser.add_argument("--league", type=str, required=True, help="League name (e.g., rpk, rbsc, ifc)")
    parser.add_argument("--gw", type=int, required=True, help="Gameweek number")

    args = parser.parse_args()
    league_name = args.league
    gw_no = args.gw

    generate_weekly_pnl_report(league_name, gw_no)

if __name__ == "__main__":
    main()

