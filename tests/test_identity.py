"""Identity tests for NPJJ30035 CONTENT.DAT container and PSP UMD ISO."""
import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SCRIPTS  # noqa: E402

sys.path.insert(0, SCRIPTS)
import content_xor  # noqa: E402
import iso9660  # noqa: E402
import vpce  # noqa: E402

ROM_DIR = ROOT / "rom"
ISO_PATH = ROM_DIR / "Benkei Gaiden (Japan) (PCE) (PSN) [NPJJ30035].iso"
CDAT_PATH = ROM_DIR / "NPJJ30035" / "CONTENT.DAT"


class IdentityTests(unittest.TestCase):
    def test_content_dat_identity(self) -> None:
        raw = CDAT_PATH.read_bytes()
        key = content_xor.find_key(raw)
        plain = content_xor.xor(raw, key)
        ents = vpce.entries(plain)
        self.assertEqual(len(ents), 25)
        repacked = vpce.pack(plain, {})
        self.assertEqual(repacked, plain)
        re_enc = content_xor.xor(repacked, key)
        self.assertEqual(re_enc, raw)

    def test_iso_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "id.iso"
            with open(ISO_PATH, "rb") as f:
                files = {p: (lba, size) for p, lba, size, _ in iso9660.listing(f)}
                lba, size = files["/PSP_GAME/PARAM.SFO"]
                f.seek(lba * 2048)
                sfo_bytes = f.read(size)
            iso9660.patch(str(ISO_PATH), str(out), {"/PSP_GAME/PARAM.SFO": sfo_bytes})
            with open(ISO_PATH, "rb") as a, open(out, "rb") as b:
                self.assertEqual(
                    hashlib.file_digest(a, "sha256").hexdigest(),
                    hashlib.file_digest(b, "sha256").hexdigest(),
                )


if __name__ == "__main__":
    unittest.main()
