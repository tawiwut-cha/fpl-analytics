# scripts/preseason_checker.py

import sys
import os
from difflib import SequenceMatcher

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

import pandas as pd
from config import ACTIVE_LEAGUES, SEASON
from data_fetch import get_league_id, get_dim_managers
from data_read_write import get_data_dir, read_dim_managers_paid, write_dim_managers

def strict_fuzzy_match(str1: str, str2: str, threshold: float = 0.85) -> bool:
    """
    Returns True if similarity ratio between normalized strings meets threshold.
    """
    if not str1 or not str2 or pd.isna(str1) or pd.isna(str2):
        return False
    
    s1, s2 = str(str1).strip().lower(), str(str2).strip().lower()
    
    if s1 == s2:
        return True
        
    return SequenceMatcher(None, s1, s2).ratio() >= threshold

def reconcile_league_payments(league_name: str, season: str = None) -> pd.DataFrame:
    """
    Reconciles dim_managers_paid.csv (team_name, whatsapp_nickname) 
    against live FPL league entries (dim_managers) using ONLY team_name matching.
    """
    selected_season = season or SEASON
    league_id = get_league_id(league_name)

    print(f"\n==========================================")
    print(f"[INFO] Preseason Audit: {league_name.upper()} ({selected_season})")
    print(f"==========================================")

    # 1. Fetch live FPL league entries
    print(f"Fetching live FPL entries for League ID {league_id}...")
    fpl_df = get_dim_managers(league_id)
    
    # Handle column name variations from FPL API standings endpoint
    fpl_team_col = 'name'
    # Construct full_name directly from first and last names
    first = fpl_df['player_first_name'].fillna('').astype(str)
    last = fpl_df['player_last_name'].fillna('').astype(str)
    fpl_df['full_name'] = (first + " " + last).str.strip()
    fpl_manager_col = 'full_name'
    
    write_dim_managers(fpl_df, league_name, season=selected_season)

    # 2. Read chat group payment file (columns: team_name, whatsapp_nickname)
    paid_df = read_dim_managers_paid(league_name, season=selected_season)
    if paid_df is None or paid_df.empty:
        print(f"[WARNING] No valid dim_managers_paid.csv found for {league_name}.")
        return fpl_df

    results = []
    fpl_matched_ids = set()

    # 3. Join strictly by team_name
    for _, paid_row in paid_df.iterrows():
        paid_team = str(paid_row.get('team_name', '')).strip()
        nickname = str(paid_row.get('whatsapp_nickname', '')).strip()
        
        matched_fpl_entry = None
        
        for _, fpl_row in fpl_df.iterrows():
            fpl_id = fpl_row.get('entry', fpl_row.get('id'))
            fpl_team = fpl_row.get(fpl_team_col, '')

            # Pure team name matching
            if strict_fuzzy_match(paid_team, fpl_team):
                matched_fpl_entry = fpl_row
                fpl_matched_ids.add(fpl_id)
                break

        if matched_fpl_entry is not None:
            fpl_id = matched_fpl_entry.get('entry', matched_fpl_entry.get('id'))
            results.append({
                "recorded_team": paid_team,
                "whatsapp_nickname": nickname,
                "fpl_entry_id": fpl_id,
                "fpl_team_name": matched_fpl_entry.get(fpl_team_col, '-'),
                "fpl_manager_name": matched_fpl_entry.get(fpl_manager_col, '-'),
                "status": "MATCHED & PAID"
            })
        else:
            results.append({
                "recorded_team": paid_team,
                "whatsapp_nickname": nickname,
                "fpl_entry_id": None,
                "fpl_team_name": "-",
                "fpl_manager_name": "-",
                "status": "PAID IN CHAT BUT NOT IN FPL LEAGUE"
            })

    # 4. Identify FPL league entries missing payment record
    for _, fpl_row in fpl_df.iterrows():
        fpl_id = fpl_row.get('entry', fpl_row.get('id'))
        if fpl_id not in fpl_matched_ids:
            results.append({
                "recorded_team": "-",
                "whatsapp_nickname": "-",
                "fpl_entry_id": fpl_id,
                "fpl_team_name": fpl_row.get(fpl_team_col, '-'),
                "fpl_manager_name": fpl_row.get(fpl_manager_col, '-'),
                "status": "JOINED FPL LEAGUE BUT UNVERIFIED PAYMENT"
            })

    audit_df = pd.DataFrame(results)

    # Summary Output
    matched_cnt = len(audit_df[audit_df['status'] == "MATCHED & PAID"])
    unjoined_cnt = len(audit_df[audit_df['status'] == "PAID IN CHAT BUT NOT IN FPL LEAGUE"])
    unpaid_cnt = len(audit_df[audit_df['status'] == "JOINED FPL LEAGUE BUT UNVERIFIED PAYMENT"])

    print(f"\n[SUMMARY] {league_name.upper()}:")
    print(f"   Total Paid Chat Records: {len(paid_df)}")
    print(f"   Total FPL League Entries: {len(fpl_df)}")
    print(f"   Fully Matched: {matched_cnt}")
    print(f"   Paid in Chat, Missing in FPL: {unjoined_cnt}")
    print(f"   Joined FPL, Unverified Payment: {unpaid_cnt}")

    # Write output
    output_dir = get_data_dir(league_name, season=selected_season)
    out_file = os.path.join(output_dir, "preseason_audit.csv")
    audit_df.to_csv(out_file, index=False)
    print(f"Saved audit report to {out_file}\n")

    return audit_df

def generate_whatsapp_messages(audit_df: pd.DataFrame, league_name: str) -> dict:
    """
    Generates clean, mention-free WhatsApp messages for each category.
    """
    messages = {}

    # 1. Fully Matched & Verified Managers
    matched = audit_df[audit_df['status'] == "MATCHED & PAID"]
    msg_matched = f"✅ *[PRESEASON AUDIT] {league_name.upper()} - VERIFIED ENTRIES*\n\n"
    msg_matched += "The following managers are fully registered and payment verified:\n\n"
    
    for _, row in matched.iterrows():
        msg_matched += f"• *{row['fpl_team_name']}* — Manager: {row['fpl_manager_name']}\n"
        
    msg_matched += "\nAll good to go for GW1! ⚽🔥"
    messages["matched"] = msg_matched

    # 2. Paid in Chat, but Haven't Joined FPL League Yet
    missing_in_fpl = audit_df[audit_df['status'] == "PAID IN CHAT BUT NOT IN FPL LEAGUE"]
    msg_missing = f"⚠️ *[ACTION REQUIRED] {league_name.upper()} - MISSING LEAGUE ENTRIES*\n\n"
    msg_missing += "Payment received, but team has not joined the FPL league standings yet:\n\n"
    
    for _, row in missing_in_fpl.iterrows():
        team = str(row.get('recorded_team', '')).strip()
        team_str = team if (team and team != '-' and not pd.isna(team)) else "Recorded Payment"
        msg_missing += f"• *{team_str}*\n"
        
    msg_missing += "\n👉 *Please join the league using the code before GW1 deadline!*"
    messages["missing_in_fpl"] = msg_missing

    # 3. Joined FPL League, but Payment Unverified / Missing
    unpaid = audit_df[audit_df['status'] == "JOINED FPL LEAGUE BUT UNVERIFIED PAYMENT"]
    msg_unpaid = f"🚨 *[ACTION REQUIRED] {league_name.upper()} - UNVERIFIED PAYMENT*\n\n"
    msg_unpaid += "The following teams are in the FPL league, but payment is pending verification:\n\n"
    
    for _, row in unpaid.iterrows():
        msg_unpaid += f"• *{row['fpl_team_name']}* — Manager: {row['fpl_manager_name']}\n"
        
    msg_unpaid += "\n👉 *Please send your payment slip in the chat to confirm your spot.*"
    messages["unpaid"] = msg_unpaid

    return messages
