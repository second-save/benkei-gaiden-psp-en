"""Build the localized PSP frontend ISO: signed EBOOT.BIN, PARAM.SFO, CONFIG.PSP, PIC0.PNG, ICON0.PNG.

    python3.14 -X utf8 tools/frontend.py   -> build/benkei_psp_en.iso

If work/eboot_jp.elf is missing, dumps it from the clean base ISO via PPSSPP (DumpFileTypes = 7).
If work/src/sign_np/sign_np is missing, compiles it via tools/build_sign_np.sh.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
from skill import SCRIPTS  # noqa: E402

sys.path.insert(0, SCRIPTS)
import iso9660  # noqa: E402
import sfo  # noqa: E402
import check_rom  # noqa: E402
import gfx_psp  # noqa: E402

TITLE = "Benkei Gaiden"
TITLE_ID = "NPJJ30035"
ELF = ROOT / "work" / "eboot_jp.elf"
ELF_SHA1 = "1b8c2e90c1243c0a2480b22ba1322592572f4abf"
SIGN_NP = Path(os.environ.get("SIGN_NP") or (ROOT / "work" / "src" / "sign_np" / "sign_np"))
OUT = ROOT / "build" / "benkei_psp_en.iso"
EBOOT_CSV = ROOT / "script" / "eboot.csv"


def ensure_sign_np() -> Path:
    if not SIGN_NP.is_file():
        subprocess.run(["bash", str(TOOLS / "build_sign_np.sh")], cwd=ROOT, check=True)
    assert SIGN_NP.is_file(), f"missing sign_np at {SIGN_NP}"
    return SIGN_NP


def ensure_eboot_elf() -> bytes:
    if not ELF.is_file():
        dump = ROOT / "work" / "pphome" / ".config" / "ppsspp" / "PSP" / "SYSTEM" / "DUMP" / f"{TITLE_ID}_EBOOT.BIN"
        dump.unlink(missing_ok=True)
        subprocess.run([sys.executable, "-X", "utf8", str(TOOLS / "pp.py"), "start", "orig", "--dump-eboot"], cwd=ROOT, check=True)
        try:
            for _ in range(40):
                if dump.is_file() and dump.stat().st_size == 708656:
                    time.sleep(0.5)
                    break
                time.sleep(0.3)
            assert dump.is_file(), f"PPSSPP did not dump {dump}"
            ELF.parent.mkdir(parents=True, exist_ok=True)
            ELF.write_bytes(dump.read_bytes())
        finally:
            subprocess.run([sys.executable, "-X", "utf8", str(TOOLS / "pp.py"), "stop"], cwd=ROOT, check=False)
    elf = ELF.read_bytes()
    got = hashlib.sha1(elf).hexdigest()
    assert got == ELF_SHA1, f"unexpected {ELF} SHA-1 {got} != {ELF_SHA1}"
    return elf


def patch_eboot(elf: bytes) -> bytes:
    b = bytearray(elf)
    with EBOOT_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            off = int(row["offset"], 16)
            jp = row["jp"].replace("\\n", "\r\n").encode("utf-8")
            en = row["en"].replace("\\n", "\r\n").encode("utf-8")
            slot = (len(jp) + 4) & ~3
            assert off % 4 == 0 and b[off : off + slot] == jp.ljust(slot, b"\0"), f"{row['offset']}: original differs"
            assert len(en) < slot, f"{row['offset']}: {len(en)} >= slot {slot}"
            assert en.count(b"%") == jp.count(b"%"), f"{row['offset']}: format codes differ"
            b[off : off + slot] = en.ljust(slot, b"\0")
    return bytes(b)


def sign(elf: bytes) -> bytes:
    """Plain ELF -> signed ~PSP EBOOT.BIN (tag 2 = 0xD9160BF0 as original)."""
    signer = ensure_sign_np()
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "in.elf"
        out = Path(d) / "EBOOT.BIN"
        src.write_bytes(elf)
        subprocess.run([str(signer), "-elf", str(src), str(out), "2"], check=True, stdout=subprocess.DEVNULL)
        signed = out.read_bytes()
    assert signed[:4] == b"~PSP" and signed[0xD0:0xD4] == bytes.fromhex("f00b16d9"), "sign_np output is not tag-2 ~PSP"
    return signed


def _iso_file(f, want: str) -> bytes:
    for path, lba, size, _ in iso9660.listing(f):
        if path == want:
            f.seek(lba * 2048)
            return f.read(size)
    raise KeyError(want)


def main() -> None:
    check_rom.check()
    isos = sorted(glob.glob(str(ROOT / "rom" / "*.iso")))
    assert len(isos) == 1, f"expected 1 ISO in rom/, got {isos}"
    src = isos[0]

    elf = ensure_eboot_elf()
    boot = patch_eboot(elf)
    signed_eboot = sign(boot)

    with open(src, "rb") as f:
        param = sfo.set_str(_iso_file(f, "/PSP_GAME/PARAM.SFO"), "TITLE", TITLE)
        config = _iso_file(f, "/PSP_GAME/USRDIR/CONFIG.PSP")
        pic = gfx_psp.make_pic0(_iso_file(f, "/PSP_GAME/PIC0.PNG"), TITLE)
        icon = gfx_psp.make_icon0(_iso_file(f, "/PSP_GAME/ICON0.PNG"))

    old_cfg = 'SYS_TITLE_JP="弁慶外伝"'.encode("utf-8")
    assert config.count(old_cfg) == 1, "expected SYS_TITLE_JP in CONFIG.PSP"
    config = config.replace(old_cfg, f'SYS_TITLE_JP="{TITLE}"'.encode("utf-8"))

    repl = {
        "/PSP_GAME/SYSDIR/EBOOT.BIN": signed_eboot,
        "/PSP_GAME/PARAM.SFO": param,
        "/PSP_GAME/USRDIR/CONFIG.PSP": config,
        "/PSP_GAME/PIC0.PNG": pic,
        "/PSP_GAME/ICON0.PNG": icon,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    iso9660.patch(src, str(OUT), repl)
    print(f"built {OUT} (sha1={hashlib.sha1(OUT.read_bytes()).hexdigest()})")


if __name__ == "__main__":
    main()
