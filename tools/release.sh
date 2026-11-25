#!/bin/bash
# Patches + zip from the current build (tools/build.py), each re-applied and compared:
#   dist/benkei-gaiden-psn-en.xdelta      CONTENT.DAT (the game, manual pages, notice screen, save icon)
#   dist/benkei-gaiden-psn-en-iso.xdelta  the ISO (emulator prompts and menus, XMB title, picture and icon)
#   dist/benkei-gaiden-psn-en.zip         both patches + README.md
# Fails if README.md does not name both built files' sha1. Publishes nothing.
set -o errexit -o pipefail
cd "$(dirname "$0")/.."
shasum -c rom.sha1
mkdir -p dist
patch() {   # original built out
  local sha; sha=$(shasum "$2" | cut -d' ' -f1)
  grep -q "$sha" README.md || { echo "README.md does not list the patched sha1 $sha ($2)"; exit 1; }
  xdelta3 -e -f -9 -B "$(stat -f %z "$1")" -s "$1" "$2" "$3"
  xdelta3 -d -c -s "$1" "$3" | cmp - "$2"
  echo "patched sha1 $sha  $2"
}
patch rom/NPJJ30035/CONTENT.DAT build/NPJJ30035/CONTENT.DAT dist/benkei-gaiden-psn-en.xdelta
patch rom/*.iso build/benkei_psp_en.iso dist/benkei-gaiden-psn-en-iso.xdelta
rm -f dist/benkei-gaiden-psn-en.zip
zip -j -q dist/benkei-gaiden-psn-en.zip dist/benkei-gaiden-psn-en.xdelta dist/benkei-gaiden-psn-en-iso.xdelta README.md
ls -l dist/benkei-gaiden-psn-en.xdelta dist/benkei-gaiden-psn-en-iso.xdelta dist/benkei-gaiden-psn-en.zip
