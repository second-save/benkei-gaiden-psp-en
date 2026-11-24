#!/bin/sh
# Frame-exact PPSSPPHeadless runner for NPJJ30035: tools/play.sh SESSION [play.py args]
# Start new session from build/ (or rom/ with "orig"): tools/play.sh new NAME [orig]
set -eu
cd "$(dirname "$0")/.."
export PPSSPP_HEADLESS="${PPSSPP_HEADLESS:-$HOME/develop/tengai-makyou-collection-psp/tools/ppsspp-headless/src/build/PPSSPPHeadless}"
PLAY="$(python3 -X utf8 tools/skill.py)/scripts/play.py"
if [ "${1:-}" = "new" ]; then
  s="work/play/$2"
  src="build"
  if [ "${3:-}" = "orig" ]; then
    src="rom"
  elif [ -n "${3:-}" ] && [ -d "${3:-}" ]; then
    src="$3"
  fi
  rm -rf "$s"
  mkdir -p "$s/memstick/PSP/GAME"
  cp -R "$src/NPJJ30035" "$s/memstick/PSP/GAME/"
  exec python3.14 -X utf8 "$PLAY" "$s" --rom "$(ls rom/*.iso)" --wait 600
fi
s="work/play/$1"
shift
exec python3.14 -X utf8 "$PLAY" "$s" "$@"
