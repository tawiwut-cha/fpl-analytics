#!/bin/bash
# run_season.sh: Orchestrates running run_weekly.sh for the entire season

# Get the directory where this script is located
SCRIPT_DIR="${0%/*}"

# Use the full path to call the weekly script
for GW in {2..38}
do
    echo "========================================"
    echo "Starting season pipeline for Gameweek $GW"
    echo "========================================"
    
    # Call the weekly script using the directory path
    bash "$SCRIPT_DIR/run_weekly.sh" "$GW"
done

echo "✅ Season complete: All 38 gameweeks processed."