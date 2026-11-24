#!/bin/bash
# Build sign_np (Hykem, github.com/swarzesherz/sign_np) in work/src/sign_np for signing patched EBOOT.BIN.
set -o errexit -o pipefail
cd "$(dirname "$0")/.."
mkdir -p work/src
[ -d work/src/sign_np ] || git clone -q https://github.com/swarzesherz/sign_np.git work/src/sign_np
cd work/src/sign_np
git checkout -q ac77d56
mkdir -p compat && echo '#include <stdlib.h>' > compat/malloc.h
rm -f ./*.o libkirk/*.o libkirk/*.a
make CFLAGS="-Icompat -I./libkirk -O2 -Wno-everything -Dfseeko64=fseeko -Dftello64=ftello -Doff64_t=off_t" >/dev/null
ls -l sign_np
