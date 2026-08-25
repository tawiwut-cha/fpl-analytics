# scripts/data_analyze.py

import pandas as pd
import numpy as np

def calc_weekly_pnl(gw_points: pd.DataFrame, league_name: str) -> pd.DataFrame:
    """
    Applies weekly PnL and ranking calculations for a given gameweek.
    
    Parameters:
    - gw_points: Raw gameweek results DataFrame.
    - league_name: Short code for the league ('rbsc', 'ifc', 'rpk').
    """
    gw = gw_points.copy()
    
    # 1. Separate Active vs Inactive managers
    # Active managers have recorded GW points or active picks
    active_mask = gw['points'] > 0
    active_managers = gw[active_mask].copy()
    inactive_managers = gw[~active_mask].copy()
    
    if active_managers.empty:
        gw['h2h_points'] = 0
        gw['rank'] = 9999
        gw['pnl'] = 0
        return gw

    # 2. Compute H2H Points & Dense Rank
    active_managers['h2h_points'] = active_managers['points'] - active_managers['transfers_cost']
    active_managers['rank'] = active_managers['h2h_points'].rank(method='dense', ascending=False).astype(int)
    
    # 3. Apply League-specific PnL rules to active subset
    league_code = league_name.lower()
    if league_code in {'rbsc', 'bpat', 'balo', 'ytce', 'jmkb'}:
        processed_active = pnl_rbsc(active_managers)
    elif league_code == 'ifc':
        processed_active = pnl_ifc(active_managers)
    elif league_code == 'rpk':
        processed_active = pnl_rpk(active_managers)
    else:
        # Default fallback: 0 PnL
        processed_active = active_managers
        processed_active['pnl'] = 0

    # 4. Handle Inactive Managers
    if not inactive_managers.empty:
        inactive_managers['h2h_points'] = 0
        inactive_managers['rank'] = 9999
        inactive_managers['pnl'] = 0
        result = pd.concat([processed_active, inactive_managers], ignore_index=True)
    else:
        result = processed_active

    # 5. Sort by rank ascending
    result = result.sort_values(by='rank', ascending=True).reset_index(drop=True)

    # 6. Verify zero-sum PnL rule
    total_pnl = result['pnl'].sum()
    if abs(total_pnl) > 5:  # Tolerance for minor rounding
        print(f"⚠️ Warning: PnL sum for {league_name} does not equal zero (Sum: {total_pnl})")

    return result


def pnl_rbsc(gw: pd.DataFrame) -> pd.DataFrame:
    """
    RBSC League Rule:
    - Worst rank(s) pay -500 THB each.
    - Winner(s) (rank == 1) split the total loser pool.
    """
    gw = gw.copy()
    ranks = list(gw['rank'])
    max_rank = max(ranks)
    min_rank = min(ranks)
    
    min_indices = [i for i, r in enumerate(ranks) if r == min_rank]
    max_indices = [i for i, r in enumerate(ranks) if r == max_rank]
    
    pnl = [0] * len(ranks)
    loser_fee = 500
    total_pool = len(max_indices) * loser_fee
    
    # Winners share pool
    prize_per_winner = round(total_pool / len(min_indices))
    for idx in min_indices:
        pnl[idx] = prize_per_winner
        
    # Losers pay fee
    for idx in max_indices:
        pnl[idx] = -loser_fee
        
    gw['pnl'] = pnl
    return gw


def pnl_ifc(gw: pd.DataFrame) -> pd.DataFrame:
    """
    IFC League Rule:
    - Bottom 3 ranks (rank >= max_rank - 2) pay -100 THB each.
    - Winner(s) (rank == min_rank) split the total loser pool.
    """
    gw = gw.copy()
    ranks = list(gw['rank'])
    max_rank = max(ranks)
    min_rank = min(ranks)
    
    min_indices = [i for i, r in enumerate(ranks) if r == min_rank]
    max_indices = [i for i, r in enumerate(ranks) if r >= max_rank - 2]
    
    pnl = [0] * len(ranks)
    loser_fee = 100
    total_pool = len(max_indices) * loser_fee
    
    # Winners share pool
    prize_per_winner = round(total_pool / len(min_indices))
    for idx in min_indices:
        pnl[idx] = prize_per_winner
        
    # Losers pay fee
    for idx in max_indices:
        pnl[idx] = -loser_fee
        
    gw['pnl'] = pnl
    return gw


def pnl_rpk(gw: pd.DataFrame) -> pd.DataFrame:
    """
    Respect Kruwai (RPK) League Rule:
    - Bottom 3 ranks pay -100 THB each.
    - Winner(s) split the total loser pool.
    """
    return pnl_ifc(gw)