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

def get_report_dir(league_name: str) -> str:
    """
    Returns the directory path for saving reports based on the league name.
    Automatically creates the folder if it doesn't exist.
    """
    path = os.path.join('outputs', '2024-2025', 'report', league_name)
    os.makedirs(path, exist_ok=True)
    return path

def read_gw_raw(league_name: str, gw_no: int):
    """
    Reads data from csv file as pd Dataframe for further usage
    """
    folder = get_data_dir(league_name)
    filename = f"gw{gw_no:02d}_raw.csv"
    filepath = os.path.join(folder, filename)
    return pd.read_csv(filepath)

def read_gw_analyzed(league_name: str, gw_no: int):
    """
    Reads data from csv file as pd Dataframe for further usage
    """
    folder = get_data_dir(league_name)
    filename = f"gw{gw_no:02d}_analyzed.csv"
    filepath = os.path.join(folder, filename)
    return pd.read_csv(filepath)

def read_dim_managers(league_name: str):
    """
    Reads dim_managers csv for further usage
    """
    folder = get_data_dir(league_name)
    filename = "dim_managers.csv"
    filepath = os.path.join(folder, filename)
    return pd.read_csv(filepath)

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
    filename = "dim_managers.csv"
    filepath = os.path.join(folder, filename)
    dim_managers.to_csv(filepath, index=False)
    print(f"{filename} saved to {folder}")

def write_report(report: str, league_name: str, gw_no: int):
    """
    Write weekly text report to reports folder.
    """
    folder = get_report_dir(league_name)
    filename = f"gw{gw_no:02d}_report.txt"
    filepath = os.path.join(folder, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"{filename} saved to {folder}")
