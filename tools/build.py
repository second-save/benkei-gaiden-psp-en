"""Build the English NPJJ30035: build/NPJJ30035/ (memory-stick folder) + build/benkei_psp_en.iso.

    python3.14 -X utf8 tools/build.py              full build
    python3.14 -X utf8 tools/build.py --identity   no replacements: asserts CONTENT.DAT rebuilds byte-identical

CONTENT.DAT -xor-> VPCE archive; replaced entries: N43302SL.PCE (the English HuCard from ../benkei-gaiden-pce),
psp_001..018.png (tools/manual.py), chyuikanki_PSP.GIM and SAVEDATA.PNG (tools/gfx_psp.py).
Then tools/frontend.py writes the ISO (EBOOT prompts, PARAM.SFO, CONFIG.PSP, PIC0, ICON0).
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402
import content_xor  # noqa: E402
import gfx_psp  # noqa: E402
import manual  # noqa: E402
import vpce  # noqa: E402

ORIG_DIR = ROOT / "rom" / "NPJJ30035"
OUT_DIR = ROOT / "build" / "NPJJ30035"
EN_PCE = ROOT.parent / "benkei-gaiden-pce" / "build" / "benkei_en.pce"
EN_PCE_SHA1 = "9e6ffc62d11803408dfceb9ad96cfcd32cbafcee"  # PCE v1.0 release build


def main() -> None:
    check_rom.check()
    identity = "--identity" in sys.argv[1:]
    enc = (ORIG_DIR / "CONTENT.DAT").read_bytes()
    key = content_xor.find_key(enc)
    plain = content_xor.xor(enc, key)
    ents = {n: plain[o : o + s] for n, o, s in vpce.entries(plain)}
    repl: dict[str, bytes] = {}
    if not identity:
        pce = EN_PCE.read_bytes()
        assert hashlib.sha1(pce).hexdigest() == EN_PCE_SHA1, f"{EN_PCE} is not the pinned English build"
        repl["N43302SL.PCE"] = pce
        for p in sorted(manual.PAGES):
            name = f"psp_{p:03d}.png"
            repl[name] = manual.page(p, ents[name])
        repl["chyuikanki_PSP.GIM"] = gfx_psp.make_chyuikanki_gim(ents["chyuikanki_PSP.GIM"])
        repl["SAVEDATA.PNG"] = gfx_psp.make_icon0(ents["SAVEDATA.PNG"])  # same art as the ISO's ICON0
    out = content_xor.xor(vpce.pack(plain, repl), key)
    if identity:
        assert out == enc, "identity build differs from the original CONTENT.DAT"
        print("identity OK")
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "CONTENT.DAT").write_bytes(out)
    for f in ("PARAM.PBP", "PSP-KEY.EDAT"):
        shutil.copy(ORIG_DIR / f, OUT_DIR / f)
    print(f"built {OUT_DIR / 'CONTENT.DAT'}  sha1 {hashlib.sha1(out).hexdigest()}  replaced {len(repl)} files")
    import frontend

    frontend.main()


if __name__ == "__main__":
    main()
