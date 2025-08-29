from data_fetch import get_league_id, get_dim_managers
from data_read_write import write_dim_managers

def update_dim_managers(league_name: str):
    # Fetch league ID from environment
    league_id = get_league_id(league_name)

    # get latest dim_managers
    dim_managers = get_dim_managers(league_id)

    # write dim manager to data folder
    write_dim_managers(dim_managers, league_name)

def main():
    """
    I want to run this function after deadline but before gw ends to get ready
    - update managers in league
    - update player names (in case of transfers)
    - get manager picks / captaincy / chips ?
    - can use trigger time from gw_status to run
    """
    for league_name in ['rbsc', 'ifc', 'rpk']:
        update_dim_managers(league_name)

if __name__ == "__main__":
    main()