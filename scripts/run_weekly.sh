#!/bin/bash
# Run reports for active leagues and gameweek

if [ -z "$1" ]; then
  echo "Usage: $0 <gameweek> [season]"
  exit 1
fi

GW=$1
SEASON=${2:-"2026-2027"}

LEAGUES=("ifc" "rpk" "rbsc")

for LEAGUE in "${LEAGUES[@]}"
do
    echo "========================================"
    echo "Processing $LEAGUE for GW$GW (Season: $SEASON)"
    echo "========================================"
    python scripts/main.py --league "$LEAGUE" --gw "$GW" --season "$SEASON"
    python scripts/report.py --league "$LEAGUE" --gw "$GW" --season "$SEASON"
done

echo "✅ All reports completed for GW$GW ($SEASON)"
