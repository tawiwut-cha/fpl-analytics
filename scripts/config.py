# scripts/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Active Season String (e.g. "2026-2027")
SEASON = os.getenv("FPL_SEASON", "2026-2027")

# Active Leagues for current season
ACTIVE_LEAGUES = ["ifc", "rpk", "rbsc"]

# League metadata & mapping
LEAGUE_CONFIGS = {
    "ifc": {
        "name": "IFC League",
        "env_var": "LEAGUE_ID_IFC",
        "pnl_rule": "pnl_ifc",
    },
    "rpk": {
        "name": "Respect Kruwai",
        "env_var": "LEAGUE_ID_RPK",
        "pnl_rule": "pnl_rpk",
    },
    "rbsc": {
        "name": "RBSC League",
        "env_var": "LEAGUE_ID_RBSC",
        "pnl_rule": "pnl_rbsc",
    },
}
