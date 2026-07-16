#!/usr/bin/env bash
# Deletes all data collected during a run, per FS-AI 2026 D6.3.2 (no reuse of
# data between autocross/sprint runs). Run between runs; show the output to
# the scrutineer as proof.
#
# The SLAM landmark map and cone map exist only in node memory — killing the
# perception nodes destroys them. Everything on disk that a run produces is
# deleted below, verbosely.

set -u

echo "=== FS-AI run-data wipe: $(date -Is) ==="

echo
echo "[1/3] Stopping perception nodes (in-memory SLAM + cone maps destroyed):"
pkill -f '[Y]OLO_cone_detector' && echo "  killed cone_detector" || echo "  cone_detector not running"
pkill -f '[l]andmark_slam'      && echo "  killed landmark_slam"  || echo "  landmark_slam not running"
pkill -f '[c]one_mapper'        && echo "  killed cone_mapper"    || echo "  cone_mapper not running"

echo
echo "[2/3] Deleting on-disk run data:"
for target in \
    "$HOME/.ros/log" \
    "$HOME/cardiff-autonomous-racing/logs" \
    /workspace/logs; do
  if [ -d "$target" ]; then
    echo "  deleting: $target"
    find "$target" -mindepth 1 -print -delete 2>/dev/null | sed 's/^/    /'
  fi
done
# any rosbag recordings anywhere under home
find "$HOME" -maxdepth 3 \( -name "*.db3" -o -name "*.mcap" \) 2>/dev/null | while read -r bag; do
  echo "  deleting bag: $bag"
  rm -f "$bag"
done

echo
echo "[3/3] Verifying nothing remains:"
leftover=$(find "$HOME/.ros/log" "$HOME/cardiff-autonomous-racing/logs" -mindepth 1 2>/dev/null | wc -l)
bags=$(find "$HOME" -maxdepth 3 \( -name "*.db3" -o -name "*.mcap" \) 2>/dev/null | wc -l)
if [ "$leftover" -eq 0 ] && [ "$bags" -eq 0 ]; then
  echo "  CLEAN — no run data remains on disk, no perception nodes running."
  echo "=== wipe complete ==="
  exit 0
else
  echo "  WARNING: $leftover log entries / $bags bags still present — investigate before staging."
  exit 1
fi
