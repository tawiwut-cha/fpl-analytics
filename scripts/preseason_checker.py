# scripts/preseason_checker.py

import argparse
import os
import pandas as pd
from config import ACTIVE_LEAGUES, SEASON
from data_fetch import get_league_id, get_dim_managers
from data_read_write import get_data_dir, read_dim_managers_paid, write_dim_managers

def fuzzy_match(str1: str, str2: str) -> bool:
    """Check if strings match loosely (case-insensitive substring or match)."""
    if not str1 or not str2:
        return False
    s1, s2 = str(str1).strip().lower(), str(str2).strip().lower()
    return s1 == s2 or s1 in s2 or s2 in s1

def reconcile_league_payments(league_name: str, season: str = None) -> pd.DataFrame:
    """
    Reconciles chat group payment records (dim_managers_paid.csv) 
    against live FPL league entries (fetched via FPL API).
    """
    selected_season = season or SEASON
    league_id = get_league_id(league_name)

    print(f"\n==========================================")
    print(f"[INFO] Preseason Audit: {league_name.upper()} ({selected_season})")
    print(f"==========================================")

    # 1. Fetch live FPL league entries
    print(f"Fetching live FPL league entries for League ID {league_id}...")
    fpl_df = get_dim_managers(league_id)
    fpl_df['full_name'] = fpl_df['player_first_name'] + " " + fpl_df['player_last_name']
    
    # Save/update local dim_managers.csv
    write_dim_managers(fpl_df, league_name, season=selected_season)

    # 2. Read chat group payment file if available
    paid_df = read_dim_managers_paid(league_name, season=selected_season)
    if paid_df is None:
        print(f"[WARNING] No dim_managers_paid.csv found in data/{selected_season}/{league_name}/.")
        print(f"[TIP] Create 'dim_managers_paid.csv' with columns: whatsapp_nickname, team_name")
        return fpl_df

    # 3. Perform matching logic
    results = []
    fpl_matched_ids = set()

    for idx, paid_row in paid_df.iterrows():
        nickname = paid_row.get('whatsapp_nickname', '')
        paid_team = paid_row.get('team_name', '')
        
        # Try finding match in FPL entries
        matched_fpl_entry = None
        for _, fpl_row in fpl_df.iterrows():
            fpl_id = fpl_row['id']
            fpl_team = fpl_row['name']
            fpl_name = fpl_row['full_name']

            if fuzzy_match(paid_team, fpl_team) or fuzzy_match(nickname, fpl_name) or fuzzy_match(nickname, fpl_team):
                matched_fpl_entry = fpl_row
                fpl_matched_ids.add(fpl_id)
                break

        if matched_fpl_entry is not None:
            status = "MATCHED & PAID"
            fpl_team_name = matched_fpl_entry['name']
            fpl_manager_name = matched_fpl_entry['full_name']
            fpl_id = matched_fpl_entry['id']
        else:
            status = "PAID IN CHAT BUT NOT IN FPL LEAGUE"
            fpl_team_name = "-"
            fpl_manager_name = "-"
            fpl_id = None

        results.append({
            "whatsapp_nickname": nickname,
            "recorded_team": paid_team,
            "fpl_entry_id": fpl_id,
            "fpl_team_name": fpl_team_name,
            "fpl_manager_name": fpl_manager_name,
            "status": status
        })

    # Find FPL entries that are NOT in paid chat records
    for _, fpl_row in fpl_df.iterrows():
        if fpl_row['id'] not in fpl_matched_ids:
            results.append({
                "whatsapp_nickname": "-",
                "recorded_team": "-",
                "fpl_entry_id": fpl_row['id'],
                "fpl_team_name": fpl_row['name'],
                "fpl_manager_name": fpl_row['full_name'],
                "status": "JOINED FPL LEAGUE BUT UNVERIFIED PAYMENT"
            })

    audit_df = pd.DataFrame(results)

    # Print summary
    matched_cnt = len(audit_df[audit_df['status'].str.contains("MATCHED")])
    unjoined_cnt = len(audit_df[audit_df['status'].str.contains("NOT IN FPL LEAGUE")])
    unpaid_cnt = len(audit_df[audit_df['status'].str.contains("UNVERIFIED PAYMENT")])

    print(f"\n[SUMMARY] {league_name.upper()}:")
    print(f"   Total Paid Chat Records: {len(paid_df)}")
    print(f"   Total FPL League Entries: {len(fpl_df)}")
    print(f"   Fully Matched: {matched_cnt}")
    print(f"   Paid in Chat, Missing in FPL: {unjoined_cnt}")
    print(f"   Joined FPL, Payment Unverified: {unpaid_cnt}")

    # Save output report
    output_dir = get_data_dir(league_name, season=selected_season)
    out_file = os.path.join(output_dir, "preseason_audit.csv")
    audit_df.to_csv(out_file, index=False)
    print(f"Saved audit report to {out_file}\n")

    return audit_df

def main():
    parser = argparse.ArgumentParser(description="Reconcile preseason entry payments with live FPL league entries.")
    parser.add_argument("--league", type=str, choices=ACTIVE_LEAGUES, help="League short code (e.g. rbsc, rpk, ifc)")
    parser.add_argument("--season", type=str, default=SEASON, help="Season string (e.g. 2026-2027 or 2025-2026)")
    args = parser.parse_args()

    leagues_to_run = [args.league] if args.league else ACTIVE_LEAGUES
    for lg in leagues_to_run:
        reconcile_league_payments(lg, season=args.season)

if __name__ == "__main__":
    main()
