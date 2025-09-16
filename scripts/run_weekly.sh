#!/bin/bash
# Run reports for multiple leagues and gameweek

# Check if GW argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <gameweek>"
  exit 1
fi

GW=$1

for LEAGUE in rbsc rpk ifc
do
    echo "Running main.py for league=$LEAGUE, gw=$GW..."
    python scripts/main.py --league "$LEAGUE" --gw "$GW"

    echo "Running report.py for league=$LEAGUE, gw=$GW..."
    python scripts/report.py --league "$LEAGUE" --gw "$GW"
done

echo "✅ All reports completed for gw=$GW"
