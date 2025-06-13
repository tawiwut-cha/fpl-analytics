import os
import pandas as pd

def get_data_dir(league_name: str) -> str:
    """
    Returns the directory path for saving data based on the league name.
    Automatically creates the folder if it doesn't exist.
    """
    path = os.path.join('data', '2024-2025', league_name)
    os.makedirs(path, exist_ok=True)
    return path

def write_gw_raw(gw_df: pd.DataFrame, league_name: str, gw_no: int):
    """
    Saves the raw gameweek data before PnL calculation.

    Parameters:
    - gw_df: DataFrame with gameweek results (no PnL)
    - league_name: short league name (e.g. 'rbsc')
    - gw_no: gameweek number
    """
    folder = get_data_dir(league_name)
    filename = f"gw{gw_no:02d}_raw.csv"
    filepath = os.path.join(folder, filename)
    gw_df.to_csv(filepath, index=False)
    print(f"Raw GW data saved to {filepath}")

def write_gw_analyzed(gw_df: pd.DataFrame, league_name: str, gw_no: int):
    """
    Saves the gameweek data with PnL calculations.

    Parameters:
    - gw_df: DataFrame with gameweek results including PnL
    - league_name: short league name (e.g. 'rbsc')
    - gw_no: gameweek number
    """
    folder = get_data_dir(league_name)
    filename = f"gw{gw_no:02d}_analyzed.csv"
    filepath = os.path.join(folder, filename)
    gw_df.to_csv(filepath, index=False)
    print(f"Analyzed GW data saved to {filepath}")

def write_preview_temp(gw_df: pd.DataFrame, filename: str = "preview.csv"):
    """
    Writes a temporary preview file for manual review before final write.

    Parameters:
    - gw_df: DataFrame to preview
    - filename: Optional custom name for the preview file
    """
    os.makedirs("temp", exist_ok=True)
    filepath = os.path.join("temp", filename)
    gw_df.to_csv(filepath, index=False)
    print(f"Preview file saved to {filepath}")

def write_dim_managers(dim_managers: pd.DataFrame, league_name: str):
    """
    Write managers names for further usage
    """
    folder = get_data_dir(league_name)
    filename = f"dim_managers.csv"
    filepath = os.path.join(folder, filename)
    dim_managers.to_csv(filepath, index=False)
    print(f"dim_managers data saved to {filepath}")
